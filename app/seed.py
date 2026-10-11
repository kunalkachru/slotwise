"""Startup seed (PLAN.md section 3).

- The studio row (and, with SEED_DEMO_DATA=true, the Isar Wellness demo data) is created
  only when the studio table is empty.
- The owner is created whenever the owners table is empty and OWNER_EMAIL / OWNER_PASSWORD
  are set, so a database first started without them can still get an owner later.
- Demo customers only ever use @example.com addresses.

Run by hand with `python -m app.seed` (uses the same environment variables as the app).
"""

import logging
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import clock
from app.config import Settings
from app.models import (
    AddOn,
    Booking,
    BookingItem,
    Customer,
    Owner,
    Service,
    Studio,
    Therapist,
    WorkingHours,
)
from app.security import hash_password, new_token

log = logging.getLogger(__name__)

STUDIO = dict(
    name="Isar Wellness",
    address="Isarstraße 12, 80469 München",
    phone="+49 89 0000 0000",
    email="hello@isar-wellness.example.com",
    opening_hours_text="Mon 10:00–19:00 · Tue–Fri 9:00–19:00 · Sat 9:00–17:00 · Sun closed",
    opening_hours_text_de="Mo 10–19 Uhr · Di–Fr 9–19 Uhr · Sa 9–17 Uhr · So geschlossen",
)

# German menu texts (name, description) and add-on names
MENU_DE = {
    "Relaxation massage": ("Entspannungsmassage", "Sanfte Ganzkörpermassage zum Abschalten."),
    "Deep tissue massage": ("Tiefengewebsmassage", "Kräftiger Druck für verspannte Muskeln."),
    "Back and neck massage": ("Rücken- und Nackenmassage",
                              "Gezielte Entlastung für Schreibtisch-Schultern."),
    "Classic facial": ("Klassische Gesichtsbehandlung", "Reinigung, Peeling, Maske und Pflege."),
    "Express facial": ("Express-Gesichtsbehandlung", "Die schnelle Frische für volle Tage."),
    "Foot reflexology": ("Fußreflexzonenmassage", "Druckpunktbehandlung der Füße."),
}
ADD_ONS_DE = {"Hot stones": "Heiße Steine", "Aromatherapy oil": "Aromaöl",
              "Eye mask treatment": "Augenmaske"}
BIOS_DE = {
    "Lena": "Massagetherapeutin mit zehn Jahren Erfahrung in Tiefengewebsmassage.",
    "Sofia": "Kosmetikerin mit Schwerpunkt Gesichtsbehandlungen und Entspannungsmassage.",
}

# (category, name, description, minutes, price, add-ons as (name, extra_minutes, price))
MASSAGE_ADD_ONS = [("Hot stones", 15, "12.00"), ("Aromatherapy oil", 0, "5.00")]
FACIAL_ADD_ONS = [("Eye mask treatment", 10, "9.00")]
MENU = [
    ("Massages", "Relaxation massage", "Slow, flowing full-body massage to switch off.",
     60, "65.00", MASSAGE_ADD_ONS),
    ("Massages", "Deep tissue massage", "Firm pressure for tight muscles and knots.",
     60, "70.00", MASSAGE_ADD_ONS),
    ("Massages", "Back and neck massage", "Focused relief for desk shoulders.",
     30, "39.00", MASSAGE_ADD_ONS),
    ("Facials", "Classic facial", "Cleanse, exfoliate, mask and moisturise.",
     45, "59.00", FACIAL_ADD_ONS),
    ("Facials", "Express facial", "A quick refresh for busy days.",
     30, "39.00", FACIAL_ADD_ONS),
    ("Reflexology", "Foot reflexology", "Pressure-point foot treatment.",
     30, "42.00", []),
]

# therapist -> (bio, services offered, weekly hours {weekday: (start, end)})
THERAPISTS = {
    "Lena": (
        "Massage therapist with ten years of experience in deep tissue work.",
        ["Relaxation massage", "Deep tissue massage", "Back and neck massage", "Foot reflexology"],
        {0: ("10:00", "19:00"), 1: ("10:00", "19:00"), 2: ("10:00", "19:00"),
         3: ("10:00", "19:00"), 4: ("10:00", "19:00"), 5: ("10:00", "14:00")},
    ),
    "Sofia": (
        "Beauty therapist specialising in facials and relaxation massage.",
        ["Classic facial", "Express facial", "Relaxation massage"],
        {1: ("09:00", "17:00"), 2: ("09:00", "17:00"), 3: ("09:00", "17:00"),
         4: ("09:00", "17:00"), 5: ("09:00", "17:00")},
    ),
}

# What each therapist's demo bookings cycle through: (service, [add-ons])
BOOKING_PATTERNS = {
    "Lena": [("Deep tissue massage", ["Hot stones"]), ("Foot reflexology", []),
             ("Relaxation massage", ["Aromatherapy oil"]), ("Back and neck massage", [])],
    "Sofia": [("Classic facial", ["Eye mask treatment"]), ("Express facial", []),
              ("Relaxation massage", [])],
}

DEMO_CUSTOMERS = [
    ("Anna", "Müller"), ("Jonas", "Klein"), ("Priya", "Shah"), ("Tom", "Becker"),
    ("Mia", "Wagner"), ("Lukas", "Schmidt"), ("Sara", "Rossi"), ("Ben", "Fischer"),
]
REPEAT_NO_SHOW = ("Ben", "Fischer")  # gets every no-show, so the owner sees the ≥2 highlight
DEMO_BOOKING_COUNT = 20


def seed(session: Session, settings: Settings) -> None:
    if session.scalar(select(func.count()).select_from(Studio)) == 0:
        session.add(Studio(**STUDIO))
        if settings.seed_demo_data:
            _seed_demo(session)
            log.info("Seeded Isar Wellness demo data.")
        else:
            log.info("Seeded studio only (SEED_DEMO_DATA is not true).")
    _ensure_owner(session, settings)
    session.commit()


def _ensure_owner(session: Session, settings: Settings) -> None:
    if session.scalar(select(func.count()).select_from(Owner)):
        return
    if not (settings.owner_email and settings.owner_password):
        log.warning("No owner account yet: set OWNER_EMAIL and OWNER_PASSWORD.")
        return
    session.add(
        Owner(
            full_name="Studio owner",
            email=settings.owner_email.strip().lower(),
            password_hash=hash_password(settings.owner_password),
        )
    )


def _hm(value: str) -> time:
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


def _seed_demo(session: Session) -> None:
    services: dict[str, Service] = {}
    for category, name, description, minutes, price, add_ons in MENU:
        name_de, description_de = MENU_DE.get(name, (None, None))
        service = Service(
            category=category, name=name, description=description,
            name_de=name_de, description_de=description_de,
            duration_minutes=minutes, price=Decimal(price), buffer_minutes=10,
        )
        service.add_ons = [
            AddOn(name=a_name, name_de=ADD_ONS_DE.get(a_name), extra_minutes=a_min,
                  price=Decimal(a_price))
            for a_name, a_min, a_price in add_ons
        ]
        services[name] = service
        session.add(service)

    therapists: dict[str, Therapist] = {}
    for name, (bio, offered, hours) in THERAPISTS.items():
        therapist = Therapist(display_name=name, short_bio=bio, short_bio_de=BIOS_DE.get(name))
        therapist.services = [services[s] for s in offered]
        therapist.working_hours = [
            WorkingHours(weekday=day, start_time=_hm(start), end_time=_hm(end))
            for day, (start, end) in hours.items()
        ]
        therapists[name] = therapist
        session.add(therapist)

    customers = {
        (first, last): Customer(
            first_name=first,
            last_name=last,
            email=f"{first}.{last}".lower().replace("ü", "ue") + "@example.com",
            phone=f"+49 151 0000 {index:04d}",
        )
        for index, (first, last) in enumerate(DEMO_CUSTOMERS, start=1)
    }
    session.add_all(customers.values())
    session.flush()

    _seed_demo_bookings(session, services, therapists, customers)


def _demo_slots(today: date) -> list[tuple[datetime, str]]:
    """Two slots per working therapist per day, from 10 days ago to 10 days ahead."""
    slots = []
    for offset in range(-10, 11):
        day = today + timedelta(days=offset)
        for name, (_, _, hours) in THERAPISTS.items():
            if day.weekday() not in hours:
                continue
            start = datetime.combine(day, _hm(hours[day.weekday()][0]), clock.BERLIN)
            slots += [(start + timedelta(hours=1), name), (start + timedelta(hours=2, minutes=30),
                                                           name)]
    return slots


def _pick_slots(today: date) -> list[tuple[datetime, str]]:
    slots = _demo_slots(today)
    todays = [s for s in slots if s[0].date() == today]
    others = [s for s in slots if s[0].date() != today]
    wanted = max(1, DEMO_BOOKING_COUNT - len(todays))
    step = max(1, len(others) // wanted)
    return sorted(todays + others[::step][:wanted])


def _seed_demo_bookings(session, services, therapists, customers) -> None:
    now = clock.now()
    regular = [c for key, c in customers.items() if key != REPEAT_NO_SHOW]
    receipt_seq = 0
    past_count = 0
    pattern_index = {name: 0 for name in THERAPISTS}

    for index, (start, therapist_name) in enumerate(_pick_slots(now.date())):
        pattern = BOOKING_PATTERNS[therapist_name]
        service_name, add_on_names = pattern[pattern_index[therapist_name] % len(pattern)]
        pattern_index[therapist_name] += 1
        service = services[service_name]
        add_ons = [a for a in service.add_ons if a.name in add_on_names]

        items = [BookingItem(item_type="service", service_id=service.id, name_snapshot=service.name,
                             minutes_snapshot=service.duration_minutes,
                             unit_price_snapshot=service.price, quantity=1)]
        items += [BookingItem(item_type="add_on", add_on_id=a.id, name_snapshot=a.name,
                              minutes_snapshot=a.extra_minutes, unit_price_snapshot=a.price,
                              quantity=1)
                  for a in add_ons]
        total_minutes = sum(i.minutes_snapshot for i in items)
        end = start + timedelta(minutes=total_minutes)

        booking = Booking(
            customer=regular[index % len(regular)],
            therapist=therapists[therapist_name],
            start_at=start,
            end_at=end,
            blocked_until=end + timedelta(minutes=service.buffer_minutes),
            total_price=sum((i.unit_price_snapshot * i.quantity for i in items), Decimal("0")),
            source=("online", "online", "phone", "online", "waitlist")[index % 5],
            manage_token=new_token(),
            items=items,
        )

        if start < now:
            past_count += 1
            if past_count % 5 == 0:
                booking.status = "no_show"
                booking.customer = customers[REPEAT_NO_SHOW]
                booking.customer.no_show_count += 1
            elif past_count % 7 == 0:
                booking.status = "cancelled"
                booking.cancelled_at = start - timedelta(hours=5)
                booking.late_cancellation = True
            else:
                booking.status = "done"
                booking.confirmed_at = start - timedelta(hours=20)
                receipt_seq += 1
                booking.receipt_number = f"IW-{start.year}-{receipt_seq:04d}"
                booking.receipt_sent_at = end + timedelta(minutes=15)
        elif start - now < timedelta(days=2):
            booking.status = "confirmed"
            booking.confirmed_at = now - timedelta(hours=1)
        else:
            booking.status = "booked"
        session.add(booking)


if __name__ == "__main__":
    from app.db import make_engine, make_session_factory
    from app.migrate import migrate

    logging.basicConfig(level=logging.INFO)
    settings = Settings.from_env()
    engine = make_engine(settings.database_url)
    migrate(engine)
    with make_session_factory(engine)() as db:
        seed(db, settings)
