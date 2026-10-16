from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import clock
from app.db import get_db
from app.emails import (
    booking_verification_email,
    confirmation_email,
    waitlist_confirm_email,
    waitlist_joined_email,
    waitlist_limit_email,
)
from app.errors import TOO_MANY_BOOKINGS, AppError
from app.i18n import category_label, request_lang
from app.logic import photos as photos_logic
from app.logic import waitlist
from app.logic.availability import chain_slots, check_date_in_range
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
    hold_until,
    mailbox_key,
    verify_booking,
)
from app.logic.calendar import booking_ics
from app.logic.selection import (
    localized,
    parse_choices,
    parse_ids,
    require_therapists,
    resolve_selection,
    therapist_candidates,
)
from app.models import CATEGORIES, Service, ServicePhoto, Studio, Therapist
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
    WaitlistConfirmOut,
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
def get_studio(request: Request, db: Session = Depends(get_db)):
    studio = db.scalar(select(Studio).limit(1))
    if studio is None:
        raise AppError(404, "The studio is not set up yet.")
    out = StudioOut.model_validate(studio)
    out.opening_hours_text = localized(
        studio.opening_hours_text, studio.opening_hours_text_de, request_lang(request))
    return out


@router.get("/services", response_model=list[CategoryOut])
def list_services(request: Request, db: Session = Depends(get_db)):
    """The public menu: active services grouped by category, each with its active add-ons."""
    services = db.scalars(
        select(Service)
        .where(Service.active.is_(True))
        .options(selectinload(Service.add_ons))
        .order_by(Service.id)
    ).all()
    lang = request_lang(request)
    photos = photos_logic.photos_by_service(db) if photos_logic.shown(db) else {}
    menu = []
    for category in CATEGORIES:
        in_category = [
            ServiceOut(
                id=s.id,
                name=localized(s.name, s.name_de, lang),
                description=localized(s.description, s.description_de, lang),
                duration_minutes=s.duration_minutes,
                price=s.price,
                add_ons=[
                    AddOnOut(id=a.id, name=localized(a.name, a.name_de, lang),
                             extra_minutes=a.extra_minutes, price=a.price)
                    for a in s.add_ons if a.active
                ],
                photo_url=photos_logic.photo_url(photos.get(s.id)),
                photo_alt=localized(photos[s.id].alt_text, photos[s.id].alt_text_de, lang)
                if s.id in photos else None,
            )
            for s in services
            if s.category == category
        ]
        if in_category:
            menu.append(CategoryOut(name=category, label=category_label(category, lang),
                                    services=in_category))
    return menu


@router.get("/therapists", response_model=list[TherapistOut])
def list_therapists(request: Request, service_ids: str = Query(""),
                    db: Session = Depends(get_db)):
    """Therapists who offer every chosen service (comma-separated ids)."""
    selection = resolve_selection(db, parse_ids(service_ids), [])
    lang = request_lang(request)
    return [TherapistOut(id=t.id, display_name=t.display_name,
                         short_bio=localized(t.short_bio, t.short_bio_de, lang))
            for t in require_therapists(db, selection)]


@router.get("/availability", response_model=AvailabilityOut)
def availability(
    date: date,
    service_ids: str = Query(""),
    add_on_ids: str = Query(""),
    therapist_id: int | None = None,
    therapist_choices: str = Query("", max_length=200),
    choose_myself: bool = False,
    db: Session = Depends(get_db),
):
    """Free chains: per treatment a therapist ("3:1,5:any"; the old `therapist_id` means one
    therapist for everything). `choose_myself` adds the chains with a 15-minute break."""
    check_date_in_range(db, date)
    selection = resolve_selection(db, parse_ids(service_ids), parse_ids(add_on_ids))
    candidates = therapist_candidates(db, selection, therapist_id,
                                      parse_choices(therapist_choices))
    slots = chain_slots(db, date, selection, candidates, choose_myself=choose_myself)
    return AvailabilityOut(date=date, total_minutes=selection.total_minutes,
                           slots=[SlotOut.from_slot(s) for s in slots])


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
            language=request_lang(request),
            therapist_choices=body.therapist_choices,
            break_before=body.break_before,
        )
    except Exception:
        limiter.release([ip_key, email_key])
        raise
    settings = request.app.state.settings
    until = hold_until(booking)
    request.app.state.mailer.send(
        booking_verification_email(booking, load_studio(db), settings.public_url, until))
    return BookingOut.from_booking(booking, first_name=body.first_name.strip(), hold_until=until)


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
        awaiting_email_confirmation=booking.status == "pending",
        hold_until=hold_until(booking) if booking.status == "pending" else None,
    )


@router.post("/bookings/{token}/verify", response_model=ManageOut)
def verify(token: str, request: Request, db: Session = Depends(get_db)):
    """The link in the "please confirm your booking" email."""
    booking = get_by_token(db, token)
    was_pending = booking.status == "pending"
    booking = verify_booking(db, booking)
    if was_pending:
        settings = request.app.state.settings
        request.app.state.mailer.send(
            confirmation_email(booking, load_studio(db), settings.public_url))
    return _manage_view(db, booking)


@router.get("/bookings/{token}", response_model=ManageOut)
def view_booking(token: str, db: Session = Depends(get_db)):
    return _manage_view(db, get_by_token(db, token))


@router.get("/services/{service_id}/photo")
def service_photo(service_id: int, db: Session = Depends(get_db)):
    """An uploaded treatment photo. Its URL carries a version stamp, so it may be cached."""
    photo = db.get(ServicePhoto, service_id)
    if photo is None or not photo.data:
        raise AppError(404, "Not found.")
    return Response(photo.data, media_type=photo.content_type, headers={
        "Cache-Control": "public, max-age=31536000, immutable",
        "X-Content-Type-Options": "nosniff",
    })


@router.get("/bookings/{token}/calendar.ics")
def booking_calendar(token: str, request: Request, db: Session = Depends(get_db)):
    """The booking as a calendar file (linked from the confirmation email and manage page)."""
    booking = get_by_token(db, token)
    studio = load_studio(db)
    public_url = request.app.state.settings.public_url
    body = booking_ics(booking, studio, f"{public_url}/manage.html?token={token}")
    day = booking.start_at.astimezone(clock.BERLIN).date().isoformat()
    return Response(body, media_type="text/calendar; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="booking-{day}.ics"',
        "Cache-Control": "no-store",
    })


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
WAITLIST_JOINS_PER_EMAIL_PER_DAY = 3


@router.post("/waitlist", response_model=WaitlistJoinOut)
def join_waitlist(body: WaitlistIn, request: Request, db: Session = Depends(get_db)):
    details = CustomerDetails(body.first_name, body.last_name, body.email, body.phone).cleaned()
    limiter = request.app.state.booking_limiter
    ip_key = "waitlist-ip:" + client_ip(
        request.client.host if request.client else None, request.headers.get("x-forwarded-for")
    )
    email_key = "waitlist-email:" + mailbox_key(details.email)
    # Per IP and per inbox, so nobody can sign a stranger up for many days of emails.
    if not limiter.try_acquire([
        (ip_key, WAITLIST_JOINS_PER_IP_PER_HOUR, 3600),
        (email_key, WAITLIST_JOINS_PER_EMAIL_PER_DAY, 86400),
    ]):
        raise AppError(429, TOO_MANY_BOOKINGS)
    try:
        result = waitlist.join(db, waitlist.JoinRequest(
            service_ids=body.service_ids, add_on_ids=body.add_on_ids,
            therapist_id=body.therapist_id, preferred_date=body.preferred_date,
            earliest_time=body.earliest_time, latest_time=body.latest_time, details=details,
            language=request_lang(request),
        ))
    except Exception:
        limiter.release([ip_key, email_key])
        raise
    studio = load_studio(db)
    mailer, public_url = request.app.state.mailer, request.app.state.settings.public_url
    # Every outcome emails the address owner; the response is the same for all of them.
    if result.outcome == "limit":
        mailer.send(waitlist_limit_email(
            result.customer, body.preferred_date, studio, waitlist.MAX_OPEN_ENTRIES_PER_CUSTOMER,
            lang=request_lang(request)))
    elif result.outcome in ("created", "unconfirmed"):
        mailer.send(waitlist_confirm_email(result.entry, studio, public_url))
    else:
        mailer.send(waitlist_joined_email(result.entry, result.position, studio, already=True))
    return WaitlistJoinOut(status="received", preferred_date=body.preferred_date)


@router.post("/waitlist/confirm/{token}", response_model=WaitlistConfirmOut)
def confirm_waitlist(token: str, request: Request, db: Session = Depends(get_db)):
    """Double opt-in link from the "please confirm" email."""
    entry = waitlist.get_entry_by_confirm_token(db, token)
    was_pending = entry is not None and entry.status == "pending"
    entry, position = waitlist.confirm_entry(db, token)
    if was_pending and position is not None:
        request.app.state.mailer.send(
            waitlist_joined_email(entry, position, load_studio(db), already=False))
    return WaitlistConfirmOut(status=entry.status, preferred_date=entry.preferred_date,
                              position=position)


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
