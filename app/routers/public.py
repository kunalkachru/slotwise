from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.emails import confirmation_email
from app.errors import TOO_MANY_BOOKINGS, AppError
from app.logic import waitlist
from app.logic.availability import check_date_in_range, free_slots
from app.logic.availability import get_studio as load_studio
from app.logic.booking import (
    CustomerDetails,
    can_cancel,
    can_confirm,
    cancel_booking,
    confirm_booking,
    create_booking,
    free_cancellation_until,
    get_by_token,
    mailbox_key,
)
from app.logic.selection import parse_ids, require_therapists, resolve_selection
from app.models import CATEGORIES, Service, Studio, Therapist
from app.schemas import (
    AddOnOut,
    AvailabilityOut,
    BookingIn,
    BookingOut,
    CategoryOut,
    ManageOut,
    OfferLineOut,
    OfferOut,
    ServiceOut,
    SlotOut,
    StudioOut,
    TherapistOut,
    WaitlistIn,
    WaitlistJoinOut,
    booking_fields,
)
from app.security import client_ip

router = APIRouter(prefix="/public", tags=["public"])

# Booking needs no login and sends an email, so cap how often one visitor or one email
# address can book (security review, slice 3): limits inbox flooding and calendar filling.
BOOKINGS_PER_IP_PER_HOUR = 10
BOOKINGS_PER_EMAIL_PER_DAY = 5


@router.get("/studio", response_model=StudioOut)
def get_studio(db: Session = Depends(get_db)):
    studio = db.scalar(select(Studio).limit(1))
    if studio is None:
        raise AppError(404, "The studio is not set up yet.")
    return studio


@router.get("/services", response_model=list[CategoryOut])
def list_services(db: Session = Depends(get_db)):
    """The public menu: active services grouped by category, each with its active add-ons."""
    services = db.scalars(
        select(Service)
        .where(Service.active.is_(True))
        .options(selectinload(Service.add_ons))
        .order_by(Service.id)
    ).all()
    menu = []
    for category in CATEGORIES:
        in_category = [
            ServiceOut(
                id=s.id,
                name=s.name,
                description=s.description,
                duration_minutes=s.duration_minutes,
                price=s.price,
                add_ons=[AddOnOut.model_validate(a) for a in s.add_ons if a.active],
            )
            for s in services
            if s.category == category
        ]
        if in_category:
            menu.append(CategoryOut(name=category, services=in_category))
    return menu


@router.get("/therapists", response_model=list[TherapistOut])
def list_therapists(service_ids: str = Query(""), db: Session = Depends(get_db)):
    """Therapists who offer every chosen service (comma-separated ids)."""
    selection = resolve_selection(db, parse_ids(service_ids), [])
    return require_therapists(db, selection)


@router.get("/availability", response_model=AvailabilityOut)
def availability(
    date: date,
    service_ids: str = Query(""),
    add_on_ids: str = Query(""),
    therapist_id: int | None = None,
    db: Session = Depends(get_db),
):
    check_date_in_range(db, date)
    selection = resolve_selection(db, parse_ids(service_ids), parse_ids(add_on_ids))
    therapists = require_therapists(db, selection)
    if therapist_id is not None:
        therapists = [t for t in therapists if t.id == therapist_id]
    slots = free_slots(db, date, selection, therapists)
    return AvailabilityOut(
        date=date,
        total_minutes=selection.total_minutes,
        slots=[
            SlotOut(
                time=s.local_time,
                start_at=s.start_at,
                therapist_id=s.therapist.id,
                therapist_name=s.therapist.display_name,
            )
            for s in slots
        ],
    )


@router.post("/bookings", response_model=BookingOut)
def book(body: BookingIn, request: Request, db: Session = Depends(get_db)):
    limiter = request.app.state.booking_limiter
    ip_key = "ip:" + client_ip(
        request.client.host if request.client else None, request.headers.get("x-forwarded-for")
    )
    # Validate first, so the limit key comes from the same canonical address the
    # confirmation email is sent to.
    details = CustomerDetails(
        body.first_name, body.last_name, body.email, body.phone, body.note
    ).cleaned()
    email_key = "email:" + mailbox_key(details.email)
    # Reserve a place under both limits before booking; give it back if booking fails.
    if not limiter.try_acquire([
        (ip_key, BOOKINGS_PER_IP_PER_HOUR, 3600),
        (email_key, BOOKINGS_PER_EMAIL_PER_DAY, 86400),
    ]):
        raise AppError(429, TOO_MANY_BOOKINGS)
    try:
        selection = resolve_selection(db, body.service_ids, body.add_on_ids)
        booking = create_booking(
            db,
            selection,
            body.date,
            body.start_time,
            body.therapist_id,
            details,
        )
    except Exception:
        limiter.release([ip_key, email_key])
        raise
    settings = request.app.state.settings
    request.app.state.mailer.send(confirmation_email(booking, load_studio(db), settings.public_url))
    return BookingOut.from_booking(booking, first_name=body.first_name.strip())


def _manage_view(db: Session, booking) -> ManageOut:
    return ManageOut(
        **booking_fields(booking),
        free_cancellation_until=free_cancellation_until(db, booking),
        late_cancellation=booking.late_cancellation,
        can_confirm=can_confirm(booking) and booking.status == "booked",
        can_cancel=can_cancel(booking),
        confirmed_at=booking.confirmed_at,
        cancelled_at=booking.cancelled_at,
        # The receipt shows only once the owner has sent it.
        receipt_number=booking.receipt_number if booking.receipt_sent_at else None,
        receipt_sent_at=booking.receipt_sent_at,
    )


@router.get("/bookings/{token}", response_model=ManageOut)
def view_booking(token: str, db: Session = Depends(get_db)):
    return _manage_view(db, get_by_token(db, token))


@router.post("/bookings/{token}/confirm", response_model=ManageOut)
def confirm(token: str, db: Session = Depends(get_db)):
    return _manage_view(db, confirm_booking(db, get_by_token(db, token)))


@router.post("/bookings/{token}/cancel", response_model=ManageOut)
def cancel(token: str, request: Request, db: Session = Depends(get_db)):
    booking = cancel_booking(db, get_by_token(db, token))
    # The freed slot goes to the first fitting person on the waitlist.
    waitlist.offer_slot(db, request.app.state.mailer, request.app.state.settings.public_url,
                        booking.therapist_id, booking.start_at)
    return _manage_view(db, booking)


# ---------- Waitlist (slice 5) ----------

WAITLIST_JOINS_PER_IP_PER_HOUR = 10


@router.post("/waitlist", response_model=WaitlistJoinOut)
def join_waitlist(body: WaitlistIn, request: Request, db: Session = Depends(get_db)):
    limiter = request.app.state.booking_limiter
    ip_key = "waitlist-ip:" + client_ip(
        request.client.host if request.client else None, request.headers.get("x-forwarded-for")
    )
    if not limiter.try_acquire([(ip_key, WAITLIST_JOINS_PER_IP_PER_HOUR, 3600)]):
        raise AppError(429, TOO_MANY_BOOKINGS)
    try:
        entry, position = waitlist.join(db, waitlist.JoinRequest(
            service_ids=body.service_ids, add_on_ids=body.add_on_ids,
            therapist_id=body.therapist_id, preferred_date=body.preferred_date,
            earliest_time=body.earliest_time, latest_time=body.latest_time,
            details=CustomerDetails(body.first_name, body.last_name, body.email, body.phone),
        ))
    except Exception:
        limiter.release([ip_key])
        raise
    return WaitlistJoinOut(position=position, preferred_date=entry.preferred_date,
                           status=entry.status)


def _offer_view(db: Session, entry) -> OfferOut:
    from app import clock
    from app.logic.selection import resolve_selection

    try:
        selection = resolve_selection(db, list(entry.service_ids), list(entry.add_on_ids))
        lines = [OfferLineOut(name=s.name, price=s.price) for s in selection.services]
        lines += [OfferLineOut(name=f"+ {a.name}", price=a.price) for a in selection.add_ons]
        minutes, total = selection.total_minutes, selection.total_price
    except AppError:
        lines, minutes, total = [], 0, 0
    local = entry.offer_start_at.astimezone(clock.BERLIN)
    status = "claimed" if entry.status == "booked" else (
        "expired" if waitlist.is_expired(entry) else "open")
    return OfferOut(
        status=status, date=local.date(), time=local.strftime("%H:%M"),
        therapist_name=db.get(Therapist, entry.offer_therapist_id).display_name,
        total_minutes=minutes, total_price=total, lines=lines,
        expires_at=entry.offer_expires_at,
    )


@router.get("/waitlist/offers/{token}", response_model=OfferOut)
def view_offer(token: str, db: Session = Depends(get_db)):
    entry = waitlist.get_offer(db, token)
    view = _offer_view(db, entry)
    if view.status == "expired":
        raise AppError(410, "Sorry, this offer has expired.")
    return view


@router.post("/waitlist/offers/{token}/claim", response_model=BookingOut)
def claim_offer(token: str, request: Request, db: Session = Depends(get_db)):
    settings = request.app.state.settings
    entry, booking = waitlist.claim(db, request.app.state.mailer, settings.public_url, token)
    request.app.state.mailer.send(confirmation_email(booking, load_studio(db), settings.public_url))
    return BookingOut.from_booking(booking, first_name=entry.customer.first_name)


@router.post("/waitlist/offers/{token}/decline", status_code=204)
def decline_offer(token: str, request: Request, db: Session = Depends(get_db)):
    from fastapi import Response

    waitlist.decline(db, request.app.state.mailer, request.app.state.settings.public_url, token)
    return Response(status_code=204)
