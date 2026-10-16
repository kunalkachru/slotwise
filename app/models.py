"""All tables (PLAN.md section 2). The schema is managed by Alembic (app/migrations):
after changing a model, add a migration (`alembic revision --autogenerate -m ...`)."""

from datetime import UTC, date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Table,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, UTCDateTime

CATEGORIES = ("Massages", "Facials", "Reflexology")
# pending: online booking waiting for the customer's email confirmation (holds the slot
# for BOOKING_HOLD_MINUTES); expired: never confirmed, or withdrawn while pending.
BOOKING_STATUSES = ("pending", "booked", "confirmed", "done", "no_show", "cancelled", "expired")
BOOKING_SOURCES = ("online", "phone", "waitlist")
ITEM_TYPES = ("service", "add_on", "extra")
# pending: joined, waiting for the email confirmation (double opt-in)
LANGUAGES = ("en", "de")
WAITLIST_STATUSES = ("pending", "waiting", "offered", "booked", "expired", "removed")

Money = Numeric(10, 2)


def _one_of(column: str, values: tuple[str, ...], name: str) -> CheckConstraint:
    allowed = ", ".join(f"'{v}'" for v in values)
    return CheckConstraint(f"{column} IN ({allowed})", name=name)


def _utcnow() -> datetime:
    from app import clock  # the one source of "now", so tests can freeze it

    return clock.now().astimezone(UTC)


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow)


class Studio(Timestamped, Base):
    __tablename__ = "studio"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    address: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(40))
    email: Mapped[str] = mapped_column(String(255))
    opening_hours_text: Mapped[str] = mapped_column(String(255), default="")
    opening_hours_text_de: Mapped[str | None] = mapped_column(String(255))
    min_notice_hours: Mapped[int] = mapped_column(default=2)
    free_cancellation_hours: Mapped[int] = mapped_column(default=24)
    booking_window_days: Mapped[int] = mapped_column(default=60)
    waitlist_offer_minutes: Mapped[int] = mapped_column(default=30)
    receipt_prefix: Mapped[str] = mapped_column(String(10), default="IW")
    # Receipts must show the VAT rate, or the small-business note (§33 UStDV): "19", "7" or
    # "small_business" (§19 UStG, no VAT charged).
    vat_mode: Mapped[str] = mapped_column(String(20), default="19", server_default="19")
    tax_number: Mapped[str | None] = mapped_column(String(40))
    show_photos: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class ServicePhoto(Base):
    """A treatment's photo. Stored in the database: Render's disk is wiped on every deploy.
    Either uploaded bytes (JPEG, PNG or WebP, resized in the owner's browser) or one of the
    built-in demo images (`demo_key`, a file under static/img/)."""

    __tablename__ = "service_photos"

    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), primary_key=True)
    content_type: Mapped[str | None] = mapped_column(String(20))
    data: Mapped[bytes | None] = mapped_column(LargeBinary)
    demo_key: Mapped[str | None] = mapped_column(String(40))
    alt_text: Mapped[str | None] = mapped_column(String(200))
    alt_text_de: Mapped[str | None] = mapped_column(String(200))
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow)


class Owner(Timestamped, Base):
    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))


therapist_services = Table(
    "therapist_services",
    Base.metadata,
    Column("therapist_id", ForeignKey("therapists.id", ondelete="CASCADE"), primary_key=True),
    Column("service_id", ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
)


class Therapist(Timestamped, Base):
    __tablename__ = "therapists"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(80), unique=True)
    short_bio: Mapped[str | None] = mapped_column(Text)
    short_bio_de: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    services: Mapped[list["Service"]] = relationship(
        secondary=therapist_services, back_populates="therapists"
    )
    working_hours: Mapped[list["WorkingHours"]] = relationship(
        back_populates="therapist", cascade="all, delete-orphan"
    )


class Service(Timestamped, Base):
    __tablename__ = "services"
    __table_args__ = (
        _one_of("category", CATEGORIES, "ck_services_category"),
        CheckConstraint(
            "duration_minutes BETWEEN 15 AND 240 AND duration_minutes % 15 = 0",
            name="ck_services_duration",
        ),
        CheckConstraint("buffer_minutes BETWEEN 0 AND 30", name="ck_services_buffer"),
        CheckConstraint("price >= 0", name="ck_services_price"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    name_de: Mapped[str | None] = mapped_column(String(120))
    description_de: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Money)
    buffer_minutes: Mapped[int] = mapped_column(default=10)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    add_ons: Mapped[list["AddOn"]] = relationship(
        back_populates="service", order_by="AddOn.id", cascade="all, delete-orphan"
    )
    therapists: Mapped[list[Therapist]] = relationship(
        secondary=therapist_services, back_populates="services"
    )


class AddOn(Timestamped, Base):
    __tablename__ = "add_ons"
    __table_args__ = (
        CheckConstraint("extra_minutes BETWEEN 0 AND 60", name="ck_add_ons_minutes"),
        CheckConstraint("price >= 0", name="ck_add_ons_price"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    name_de: Mapped[str | None] = mapped_column(String(120))
    extra_minutes: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Money)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    service: Mapped[Service] = relationship(back_populates="add_ons")


class WorkingHours(Timestamped, Base):
    __tablename__ = "working_hours"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_working_hours_weekday"),
        CheckConstraint("end_time > start_time", name="ck_working_hours_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    therapist_id: Mapped[int] = mapped_column(ForeignKey("therapists.id", ondelete="CASCADE"))
    weekday: Mapped[int] = mapped_column(Integer)  # 0 = Monday … 6 = Sunday
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    therapist: Mapped[Therapist] = relationship(back_populates="working_hours")


class DayOff(Timestamped, Base):
    __tablename__ = "days_off"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NULL = the whole studio is closed that day
    therapist_id: Mapped[int | None] = mapped_column(
        ForeignKey("therapists.id", ondelete="CASCADE")
    )
    date: Mapped[date] = mapped_column(Date)
    reason: Mapped[str | None] = mapped_column(String(120))


class Customer(Timestamped, Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(255), unique=True)  # stored lower-case
    phone: Mapped[str] = mapped_column(String(40))
    no_show_count: Mapped[int] = mapped_column(default=0)
    anonymized_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="customer")


class Booking(Timestamped, Base):
    __tablename__ = "bookings"
    __table_args__ = (
        _one_of("status", BOOKING_STATUSES, "ck_bookings_status"),
        _one_of("source", BOOKING_SOURCES, "ck_bookings_source"),
        CheckConstraint("end_at > start_at", name="ck_bookings_end"),
        CheckConstraint("blocked_until >= end_at", name="ck_bookings_blocked"),
        Index("ix_bookings_therapist_start", "therapist_id", "start_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    therapist_id: Mapped[int] = mapped_column(ForeignKey("therapists.id"))
    start_at: Mapped[datetime] = mapped_column(UTCDateTime)
    end_at: Mapped[datetime] = mapped_column(UTCDateTime)
    # end_at + largest buffer of the booked services, frozen at booking time
    blocked_until: Mapped[datetime] = mapped_column(UTCDateTime)
    status: Mapped[str] = mapped_column(String(20), default="booked")
    total_price: Mapped[Decimal] = mapped_column(Money)
    source: Mapped[str] = mapped_column(String(20), default="online")
    manage_token: Mapped[str] = mapped_column(String(64), unique=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    late_cancellation: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    receipt_number: Mapped[str | None] = mapped_column(String(30), unique=True)
    receipt_sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    customer_note: Mapped[str | None] = mapped_column(String(300))
    # Language the customer booked in: emails about this booking use it.
    language: Mapped[str] = mapped_column(String(2), default="en", server_default="en")

    customer: Mapped[Customer] = relationship(back_populates="bookings")
    therapist: Mapped[Therapist] = relationship()
    items: Mapped[list["BookingItem"]] = relationship(
        back_populates="booking", order_by="BookingItem.id", cascade="all, delete-orphan"
    )


class BookingItem(Timestamped, Base):
    __tablename__ = "booking_items"
    __table_args__ = (
        _one_of("item_type", ITEM_TYPES, "ck_booking_items_type"),
        CheckConstraint("quantity >= 1", name="ck_booking_items_quantity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"))
    item_type: Mapped[str] = mapped_column(String(20))
    service_id: Mapped[int | None] = mapped_column(ForeignKey("services.id"))
    add_on_id: Mapped[int | None] = mapped_column(ForeignKey("add_ons.id"))
    # Snapshots: copied at booking time and never re-read from the menu.
    name_snapshot: Mapped[str] = mapped_column(String(120))
    minutes_snapshot: Mapped[int] = mapped_column(Integer, default=0)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Money)
    quantity: Mapped[int] = mapped_column(default=1)

    booking: Mapped[Booking] = relationship(back_populates="items")


class WaitlistEntry(Timestamped, Base):
    __tablename__ = "waitlist_entries"
    __table_args__ = (_one_of("status", WAITLIST_STATUSES, "ck_waitlist_entries_status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    therapist_id: Mapped[int | None] = mapped_column(ForeignKey("therapists.id"))  # NULL = any
    service_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    add_on_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    preferred_date: Mapped[date] = mapped_column(Date)
    earliest_time: Mapped[time] = mapped_column(Time)
    latest_time: Mapped[time] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(20), default="waiting")
    confirm_token: Mapped[str | None] = mapped_column(String(64), unique=True)  # opt-in link
    offer_token: Mapped[str | None] = mapped_column(String(64), unique=True)
    offer_start_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    offer_therapist_id: Mapped[int | None] = mapped_column(ForeignKey("therapists.id"))
    offer_expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    offered_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id"))
    language: Mapped[str] = mapped_column(String(2), default="en", server_default="en")

    customer: Mapped[Customer] = relationship()
