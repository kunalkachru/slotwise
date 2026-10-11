from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app import clock
from app.db import get_db
from app.emails import confirmation_email, receipt_email
from app.logic import catalog, waitlist
from app.logic import dashboard as dashboard_logic
from app.logic.availability import check_date_in_range, free_slots, get_studio
from app.logic.booking import CustomerDetails, create_booking
from app.logic.owner_bookings import (
    REPEAT_NO_SHOW_THRESHOLD,
    ItemInput,
    assign_receipt_number,
    bookings_csv,
    change_status,
    get_booking,
    has_started,
    list_bookings,
    replace_items,
)
from app.logic.selection import parse_ids, require_therapists, resolve_selection
from app.models import Owner, Therapist
from app.routers.auth import current_owner, same_origin
from app.schemas import (
    AddOnAdminOut,
    AddOnIn,
    AvailabilityOut,
    BookingIn,
    DashboardOut,
    DayOffIn,
    DayOffOut,
    HoursListIn,
    ItemsIn,
    OwnerBookingOut,
    OwnerWaitlistOut,
    ServiceAdminOut,
    ServiceIn,
    SlotOut,
    StatusIn,
    StudioSettings,
    TherapistAdminOut,
    TherapistIn,
)

# Every route here requires the owner session; changes must come from this site.
router = APIRouter(
    prefix="/owner", tags=["owner"], dependencies=[Depends(current_owner), Depends(same_origin)]
)

MAX_RANGE_DAYS = 92


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    date: date | None = None,
    owner: Owner = Depends(current_owner),
    db: Session = Depends(get_db),
):
    day = date or clock.now().date()
    d = dashboard_logic.build(db, day)
    return DashboardOut(
        date=day.isoformat(),
        owner_name=owner.full_name,
        window_start=d.window_start,
        today_bookings=d.today_bookings,
        expected_revenue_today=d.expected_revenue_today,
        confirmation_rate_today=d.confirmation_rate_today,
        no_show_rate=d.no_show_rate,
        refill_rate=d.refill_rate,
        revenue_recovered=d.revenue_recovered,
        online_share=d.online_share,
        targets=dashboard_logic.TARGETS,
        weeks=[{"week_start": w.week_start, "no_shows": w.no_shows,
                "late_cancellations": w.late_cancellations} for w in d.weeks],
        appointments=dashboard_logic.appointment_rows(d),
    )


# ---------- Bookings ----------


def _out(booking) -> OwnerBookingOut:
    return OwnerBookingOut.from_booking(booking, has_started(booking), REPEAT_NO_SHOW_THRESHOLD)


def _range(from_: date | None, to: date | None) -> tuple[date, date]:
    start = from_ or clock.now().date()
    end = to or start + timedelta(days=6)
    if end < start or (end - start).days > MAX_RANGE_DAYS:
        from app.errors import AppError

        raise AppError(422, "Please choose a range of up to 3 months.", field="to")
    return start, end


@router.get("/bookings", response_model=list[OwnerBookingOut])
def bookings(
    from_: date | None = Query(None, alias="from"),
    to: date | None = None,
    therapist_id: int | None = None,
    status: str | None = None,
    q: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
):
    start, end = _range(from_, to)
    return [_out(b) for b in list_bookings(db, start, end, therapist_id, status, q)]


@router.get("/bookings/export.csv")
def export_csv(
    from_: date | None = Query(None, alias="from"),
    to: date | None = None,
    therapist_id: int | None = None,
    status: str | None = None,
    q: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
):
    start, end = _range(from_, to)
    body = bookings_csv(list_bookings(db, start, end, therapist_id, status, q))
    return Response(
        content="﻿" + body,  # BOM so Excel reads UTF-8 names correctly
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="bookings-{start}-to-{end}.csv"',
                 "Cache-Control": "no-store"},
    )


@router.get("/bookings/{booking_id}", response_model=OwnerBookingOut)
def booking_detail(booking_id: int, db: Session = Depends(get_db)):
    return _out(get_booking(db, booking_id))


@router.get("/availability", response_model=AvailabilityOut)
def owner_availability(
    date: date,
    service_ids: str = Query(""),
    add_on_ids: str = Query(""),
    therapist_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Like the public endpoint, but without the 2-hour notice (phone bookings)."""
    check_date_in_range(db, date)
    selection = resolve_selection(db, parse_ids(service_ids), parse_ids(add_on_ids))
    therapists = require_therapists(db, selection)
    if therapist_id is not None:
        therapists = [t for t in therapists if t.id == therapist_id]
    slots = free_slots(db, date, selection, therapists, for_owner=True)
    return AvailabilityOut(
        date=date, total_minutes=selection.total_minutes,
        slots=[SlotOut(time=s.local_time, start_at=s.start_at, therapist_id=s.therapist.id,
                       therapist_name=s.therapist.display_name) for s in slots],
    )


@router.post("/bookings", response_model=OwnerBookingOut)
def phone_booking(body: BookingIn, request: Request, db: Session = Depends(get_db)):
    selection = resolve_selection(db, body.service_ids, body.add_on_ids)
    booking = create_booking(
        db, selection, body.date, body.start_time, body.therapist_id,
        CustomerDetails(body.first_name, body.last_name, body.email, body.phone, body.note),
        source="phone",
    )
    settings = request.app.state.settings
    request.app.state.mailer.send(confirmation_email(booking, get_studio(db), settings.public_url))
    return _out(get_booking(db, booking.id))


@router.put("/bookings/{booking_id}/status", response_model=OwnerBookingOut)
def set_status(booking_id: int, body: StatusIn, request: Request, db: Session = Depends(get_db)):
    booking = get_booking(db, booking_id)
    was_freed = booking.status in ("cancelled", "expired")
    booking = change_status(db, booking, body.status)
    if booking.status in ("cancelled", "expired") and not was_freed:
        waitlist.offer_slot(db, request.app.state.mailer,
                            request.app.state.settings.public_url,
                            booking.therapist_id, booking.start_at)
    return _out(booking)


@router.put("/bookings/{booking_id}/items", response_model=OwnerBookingOut)
def set_items(booking_id: int, body: ItemsIn, db: Session = Depends(get_db)):
    items = [ItemInput(**i.model_dump()) for i in body.items]
    return _out(replace_items(db, get_booking(db, booking_id), items))


@router.post("/bookings/{booking_id}/receipt", response_model=OwnerBookingOut)
def send_receipt(booking_id: int, request: Request, db: Session = Depends(get_db)):
    booking = assign_receipt_number(db, get_booking(db, booking_id))
    settings = request.app.state.settings
    request.app.state.mailer.send(receipt_email(booking, get_studio(db), settings.public_url))
    return _out(booking)


# ---------- Services & add-ons ----------


@router.get("/services", response_model=list[ServiceAdminOut])
def services(db: Session = Depends(get_db)):
    return catalog.list_services(db)


@router.post("/services", response_model=ServiceAdminOut)
def create_service(body: ServiceIn, db: Session = Depends(get_db)):
    return catalog.save_service(db, catalog.ServiceInput(**body.model_dump()))


@router.put("/services/{service_id}", response_model=ServiceAdminOut)
def update_service(service_id: int, body: ServiceIn, db: Session = Depends(get_db)):
    return catalog.save_service(db, catalog.ServiceInput(**body.model_dump()), service_id)


@router.post("/add-ons", response_model=AddOnAdminOut)
def create_add_on(body: AddOnIn, db: Session = Depends(get_db)):
    return catalog.save_add_on(db, catalog.AddOnInput(**body.model_dump()))


@router.put("/add-ons/{add_on_id}", response_model=AddOnAdminOut)
def update_add_on(add_on_id: int, body: AddOnIn, db: Session = Depends(get_db)):
    return catalog.save_add_on(db, catalog.AddOnInput(**body.model_dump()), add_on_id)


# ---------- Therapists, hours, days off ----------


@router.get("/therapists", response_model=list[TherapistAdminOut])
def therapists(db: Session = Depends(get_db)):
    return [TherapistAdminOut.from_therapist(t) for t in catalog.list_therapists(db)]


@router.post("/therapists", response_model=TherapistAdminOut)
def create_therapist(body: TherapistIn, db: Session = Depends(get_db)):
    return TherapistAdminOut.from_therapist(
        catalog.save_therapist(db, catalog.TherapistInput(**body.model_dump())))


@router.put("/therapists/{therapist_id}", response_model=TherapistAdminOut)
def update_therapist(therapist_id: int, body: TherapistIn, db: Session = Depends(get_db)):
    return TherapistAdminOut.from_therapist(
        catalog.save_therapist(db, catalog.TherapistInput(**body.model_dump()), therapist_id))


@router.put("/therapists/{therapist_id}/hours", response_model=TherapistAdminOut)
def set_hours(therapist_id: int, body: HoursListIn, db: Session = Depends(get_db)):
    hours = [catalog.HoursInput(**h.model_dump()) for h in body.hours]
    return TherapistAdminOut.from_therapist(catalog.replace_hours(db, therapist_id, hours))


def _day_off_out(db: Session, d) -> DayOffOut:
    therapist = db.get(Therapist, d.therapist_id) if d.therapist_id else None
    return DayOffOut(id=d.id, therapist_id=d.therapist_id,
                     therapist_name=therapist.display_name if therapist else None,
                     date=d.date, reason=d.reason)


@router.get("/days-off", response_model=list[DayOffOut])
def days_off(from_: date | None = Query(None, alias="from"), db: Session = Depends(get_db)):
    return [_day_off_out(db, d) for d in catalog.list_days_off(db, from_ or clock.now().date())]


@router.post("/days-off", response_model=DayOffOut)
def add_day_off(body: DayOffIn, db: Session = Depends(get_db)):
    return _day_off_out(db, catalog.add_day_off(db, body.therapist_id, body.date, body.reason))


@router.delete("/days-off/{day_off_id}", status_code=204)
def delete_day_off(day_off_id: int, db: Session = Depends(get_db)) -> Response:
    catalog.delete_day_off(db, day_off_id)
    return Response(status_code=204)


# ---------- Waitlist ----------


def _waitlist_out(db: Session, e) -> OwnerWaitlistOut:
    from app.models import AddOn, Service

    names = [db.get(Service, i).name for i in e.service_ids if db.get(Service, i)]
    names += [f"+ {db.get(AddOn, i).name}" for i in e.add_on_ids if db.get(AddOn, i)]
    therapist = db.get(Therapist, e.therapist_id) if e.therapist_id else None
    return OwnerWaitlistOut(
        id=e.id, customer_name=f"{e.customer.first_name} {e.customer.last_name}",
        email=e.customer.email, phone=e.customer.phone, services=names,
        preferred_date=e.preferred_date, earliest_time=e.earliest_time.strftime("%H:%M"),
        latest_time=e.latest_time.strftime("%H:%M"),
        therapist_name=therapist.display_name if therapist else None,
        joined_at=e.created_at, status=e.status, offered_at=e.offered_at,
        offer_expires_at=e.offer_expires_at,
        offer_time=e.offer_start_at.astimezone(clock.BERLIN).strftime("%a %-d %b %H:%M")
        if e.offer_start_at else None,
        booking_id=e.booking_id,
    )


@router.get("/waitlist", response_model=list[OwnerWaitlistOut])
def owner_waitlist(date: date | None = None, db: Session = Depends(get_db)):
    return [_waitlist_out(db, e) for e in waitlist.list_entries(db, date)]


@router.delete("/waitlist/{entry_id}", status_code=204)
def remove_waitlist_entry(entry_id: int, db: Session = Depends(get_db)) -> Response:
    waitlist.remove_entry(db, entry_id)
    return Response(status_code=204)


# ---------- Studio settings ----------


@router.get("/studio", response_model=StudioSettings)
def studio_settings(db: Session = Depends(get_db)):
    return get_studio(db)


@router.put("/studio", response_model=StudioSettings)
def update_studio(body: StudioSettings, db: Session = Depends(get_db)):
    return catalog.save_studio(db, catalog.StudioInput(**body.model_dump()))
