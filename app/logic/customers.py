"""GDPR requests from a customer: a copy of their data (access) or erasure."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import clock
from app.errors import AppError
from app.logic.jobs import anonymize_customer
from app.models import Customer, WaitlistEntry


def get_customer(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise AppError(404, "Not found.")
    return customer


def export(db: Session, customer: Customer) -> dict:
    """Everything stored about the customer, for an access request (Art. 15 GDPR).
    Links and tokens are left out: they are keys, not personal data."""
    def local(moment):
        return moment.astimezone(clock.BERLIN).isoformat(timespec="minutes") if moment else None

    entries = db.scalars(select(WaitlistEntry).where(WaitlistEntry.customer_id == customer.id)
                         .order_by(WaitlistEntry.id)).all()
    return {
        "exported_at": local(clock.now()),
        "customer": {
            "first_name": customer.first_name, "last_name": customer.last_name,
            "email": customer.email, "phone": customer.phone,
            "no_shows": customer.no_show_count, "anonymized_at": local(customer.anonymized_at),
        },
        "bookings": [{
            "start": local(b.start_at), "end": local(b.end_at), "status": b.status,
            "therapist": b.therapist.display_name, "source": b.source,
            "items": [{"name": i.name_snapshot, "quantity": i.quantity,
                       "unit_price": str(i.unit_price_snapshot)} for i in b.items],
            "total_price": str(b.total_price), "receipt_number": b.receipt_number,
            "note": b.customer_note, "booked_at": local(b.created_at),
        } for b in sorted(customer.bookings, key=lambda b: b.start_at)],
        "waitlist": [{
            "day": e.preferred_date.isoformat(), "from": e.earliest_time.strftime("%H:%M"),
            "until": e.latest_time.strftime("%H:%M"), "status": e.status,
            "joined_at": local(e.created_at),
        } for e in entries],
    }


def erase(db: Session, customer: Customer) -> Customer:
    """Erasure (Art. 17 GDPR): the same anonymization as the 2-year clean-up. Bookings and
    receipts keep their dates and amounts, which tax law requires."""
    if customer.anonymized_at is None:
        anonymize_customer(db, customer)
        db.commit()
    return customer
