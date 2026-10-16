from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

from app.clock import BERLIN

# Money leaves the API as a string with exactly two decimals ("70.00"), never a float.
MoneyStr = Annotated[
    Decimal, PlainSerializer(lambda v: f"{v.quantize(Decimal('0.01'))}", return_type=str)
]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthOut(BaseModel):
    status: str
    version: str


class StudioOut(ORMModel):
    name: str
    address: str
    phone: str
    email: str
    opening_hours_text: str
    min_notice_hours: int
    free_cancellation_hours: int
    booking_window_days: int
    vat_mode: str  # for the receipt: "19", "7" or "small_business"
    tax_number: str | None


class AddOnOut(ORMModel):
    id: int
    name: str
    extra_minutes: int
    price: MoneyStr


class ServiceOut(ORMModel):
    id: int
    name: str
    description: str | None
    duration_minutes: int
    price: MoneyStr
    add_ons: list[AddOnOut]
    photo_url: str | None = None  # None: no photo, or photos switched off
    photo_alt: str | None = None  # the owner's description of the photo, in the page language


class CategoryOut(BaseModel):
    name: str  # stable key (English)
    label: str = ""  # shown to the customer, in their language
    services: list[ServiceOut]


class LoginIn(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=200)


class OwnerOut(ORMModel):
    id: int
    full_name: str
    email: str


class WeekOut(BaseModel):
    week_start: date
    no_shows: int
    late_cancellations: int


class DashboardAppointmentOut(BaseModel):
    id: int
    time: str
    customer_name: str
    repeat_no_show: bool
    therapist_name: str
    services: list[str]
    total_price: MoneyStr
    status: str


class DashboardOut(BaseModel):
    date: str
    owner_name: str
    window_start: date | None = None
    today_bookings: int = 0
    expected_revenue_today: MoneyStr = Decimal(0)
    confirmation_rate_today: float | None = None
    no_show_rate: float | None = None
    refill_rate: float | None = None
    revenue_recovered: MoneyStr = Decimal(0)
    online_share: float | None = None
    targets: dict[str, float] = Field(default_factory=dict)
    weeks: list[WeekOut] = Field(default_factory=list)
    appointments: list[DashboardAppointmentOut] = Field(default_factory=list)


# ---------- Slice 2: availability and booking ----------


class TherapistOut(ORMModel):
    id: int
    display_name: str
    short_bio: str | None


class StepOut(BaseModel):
    """One treatment of a chain: when it runs and who does it."""
    service_id: int
    therapist_id: int
    therapist_name: str
    time: str  # "11:15", Europe/Berlin
    end_time: str
    start_at: datetime


class SlotOut(BaseModel):
    time: str  # "17:00", Europe/Berlin
    start_at: datetime
    therapist_id: int  # the first treatment's therapist
    therapist_name: str
    steps: list[StepOut] = Field(default_factory=list)
    break_before: int | None = None  # the treatment that follows a 15-minute break

    @classmethod
    def from_slot(cls, slot) -> "SlotOut":
        def hm(moment: datetime) -> str:
            return moment.astimezone(BERLIN).strftime("%H:%M")

        return cls(
            time=slot.local_time, start_at=slot.start_at, therapist_id=slot.therapist.id,
            therapist_name=slot.therapist.display_name, break_before=slot.break_before,
            steps=[StepOut(service_id=s.service_id, therapist_id=s.therapist.id,
                           therapist_name=s.therapist.display_name, time=hm(s.start_at),
                           end_time=hm(s.end_at), start_at=s.start_at) for s in slot.steps],
        )


class AvailabilityOut(BaseModel):
    date: date
    total_minutes: int
    slots: list[SlotOut]


class BookingIn(BaseModel):
    service_ids: list[int] = Field(min_length=1, max_length=10)
    add_on_ids: list[int] = Field(default_factory=list, max_length=20)
    therapist_id: int | None = None  # one therapist for everything (the old API)
    # Per treatment: service id -> therapist id, or null for "No preference" (option B).
    therapist_choices: dict[int, int | None] | None = Field(default=None, max_length=10)
    break_before: int | None = Field(default=None, ge=1, le=9)
    date: date
    start_time: str = Field(max_length=5)
    first_name: str = Field(max_length=80)
    last_name: str = Field(max_length=80)
    email: str = Field(max_length=255)
    phone: str = Field(max_length=40)
    note: str | None = Field(default=None, max_length=1000)


class BookingItemOut(ORMModel):
    item_type: str
    name: str
    minutes: int
    unit_price: MoneyStr
    quantity: int
    line_total: MoneyStr
    segment_position: int | None = None  # which part of the visit (option B); None = extra


class SegmentOut(BaseModel):
    """One therapist's part of a visit, for the owner's calendar."""
    position: int
    therapist_id: int
    therapist_name: str
    time: str  # Europe/Berlin
    end_time: str


class PlanLineOut(BaseModel):
    time: str  # Europe/Berlin
    end_time: str
    therapist_name: str | None
    names: list[str]
    is_break: bool


def plan_out(booking) -> list[PlanLineOut]:
    def hm(moment: datetime) -> str:
        return moment.astimezone(BERLIN).strftime("%H:%M")

    return [PlanLineOut(time=hm(line.start_at), end_time=hm(line.end_at),
                        therapist_name=line.therapist_name, names=line.names,
                        is_break=line.is_break) for line in booking.visit_plan()]


def booking_fields(booking) -> dict:
    local_start = booking.start_at.astimezone(BERLIN)
    return dict(
        status=booking.status,
        source=booking.source,
        start_at=booking.start_at,
        end_at=booking.end_at,
        date=local_start.date(),
        time=local_start.strftime("%H:%M"),
        total_minutes=sum(i.minutes_snapshot * i.quantity for i in booking.items),
        total_price=booking.total_price,
        therapist_name=booking.therapist_names,
        # Several therapists (option B): who does what, when. One line for a simple booking.
        visit=plan_out(booking),
        items=[
            BookingItemOut(
                item_type=i.item_type,
                name=i.name_snapshot,
                minutes=i.minutes_snapshot,
                unit_price=i.unit_price_snapshot,
                quantity=i.quantity,
                line_total=i.unit_price_snapshot * i.quantity,
                segment_position=i.segment.position if i.segment else None,
            )
            for i in booking.items
        ],
    )


class BookingOut(BaseModel):
    """Returned right after booking."""

    id: int
    status: str
    source: str
    start_at: datetime
    end_at: datetime
    date: date
    time: str
    total_minutes: int
    total_price: MoneyStr
    therapist_name: str
    visit: list[PlanLineOut] = Field(default_factory=list)
    customer_first_name: str
    items: list[BookingItemOut]
    hold_until: datetime | None = None  # set while the booking awaits email confirmation

    @classmethod
    def from_booking(cls, booking, first_name: str, hold_until=None) -> "BookingOut":
        """`first_name` is the name submitted with this booking. Never echo the saved
        customer's name: the booker may not be that customer (security review).
        The manage token is deliberately absent: it only travels by email, which is
        what proves the booker owns the address."""
        return cls(
            id=booking.id,
            customer_first_name=first_name,
            hold_until=hold_until,
            **booking_fields(booking),
        )


class ManageOut(BaseModel):
    """What the secret manage link shows. Deliberately no customer details: the link
    holder is not necessarily the person whose email the booking uses."""

    status: str
    source: str
    start_at: datetime
    end_at: datetime
    date: date
    time: str
    total_minutes: int
    total_price: MoneyStr
    therapist_name: str
    visit: list[PlanLineOut] = Field(default_factory=list)
    items: list[BookingItemOut]
    free_cancellation_until: datetime
    late_cancellation: bool
    can_confirm: bool
    can_cancel: bool
    confirmed_at: datetime | None
    cancelled_at: datetime | None
    receipt_number: str | None = None
    receipt_sent_at: datetime | None = None
    awaiting_email_confirmation: bool = False
    hold_until: datetime | None = None


# ---------- Slice 4: owner area ----------


class OwnerCustomerOut(ORMModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: str
    no_show_count: int
    repeat_no_show: bool


class OwnerBookingOut(BaseModel):
    id: int
    status: str
    source: str
    start_at: datetime
    end_at: datetime
    date: date
    time: str
    total_minutes: int
    total_price: MoneyStr
    therapist_id: int
    therapist_name: str
    visit: list[PlanLineOut] = Field(default_factory=list)
    segments: list[SegmentOut] = Field(default_factory=list)
    items: list[BookingItemOut]
    customer: OwnerCustomerOut
    customer_note: str | None
    late_cancellation: bool
    confirmed_at: datetime | None
    cancelled_at: datetime | None
    receipt_number: str | None
    receipt_sent_at: datetime | None
    has_started: bool
    manage_token: str | None = None

    @classmethod
    def from_booking(cls, booking, has_started: bool, threshold: int) -> "OwnerBookingOut":
        c = booking.customer

        def hm(moment: datetime) -> str:
            return moment.astimezone(BERLIN).strftime("%H:%M")

        return cls(
            id=booking.id,
            therapist_id=booking.therapist_id,
            segments=[SegmentOut(position=s.position, therapist_id=s.therapist_id,
                                 therapist_name=s.therapist.display_name,
                                 time=hm(s.start_at), end_time=hm(s.end_at))
                      for s in booking.segments],
            customer=OwnerCustomerOut(
                id=c.id, first_name=c.first_name, last_name=c.last_name, email=c.email,
                phone=c.phone, no_show_count=c.no_show_count,
                repeat_no_show=c.no_show_count >= threshold,
            ),
            customer_note=booking.customer_note,
            late_cancellation=booking.late_cancellation,
            confirmed_at=booking.confirmed_at,
            cancelled_at=booking.cancelled_at,
            receipt_number=booking.receipt_number,
            receipt_sent_at=booking.receipt_sent_at,
            has_started=has_started,
            **booking_fields(booking),
        )


class StatusIn(BaseModel):
    status: str = Field(max_length=20)


class ItemIn(BaseModel):
    item_type: str = Field(max_length=10)
    name: str = Field(max_length=120)
    minutes: int = 0
    unit_price: Decimal
    quantity: int = 1
    service_id: int | None = None
    add_on_id: int | None = None
    segment_position: int | None = Field(default=None, ge=0, le=9)


class ItemsIn(BaseModel):
    items: list[ItemIn] = Field(min_length=1, max_length=30)


class AddOnAdminOut(ORMModel):
    id: int
    service_id: int
    name: str
    name_de: str | None = None
    extra_minutes: int
    price: MoneyStr
    active: bool


class ServiceAdminOut(ORMModel):
    id: int
    category: str
    name: str
    description: str | None
    name_de: str | None = None
    description_de: str | None = None
    duration_minutes: int
    price: MoneyStr
    buffer_minutes: int
    active: bool
    add_ons: list[AddOnAdminOut]


class ServiceIn(BaseModel):
    category: str = Field(max_length=40)
    name: str = Field(max_length=120)
    description: str | None = Field(default=None, max_length=500)
    name_de: str | None = Field(default=None, max_length=120)
    description_de: str | None = Field(default=None, max_length=500)
    duration_minutes: int
    price: Decimal
    buffer_minutes: int = 10
    active: bool = True


class AddOnIn(BaseModel):
    service_id: int
    name: str = Field(max_length=120)
    name_de: str | None = Field(default=None, max_length=120)
    extra_minutes: int = 0
    price: Decimal
    active: bool = True


class HoursOut(BaseModel):
    weekday: int
    start_time: str
    end_time: str


class TherapistAdminOut(BaseModel):
    id: int
    display_name: str
    short_bio: str | None
    short_bio_de: str | None = None
    active: bool
    service_ids: list[int]
    hours: list[HoursOut]

    @classmethod
    def from_therapist(cls, t) -> "TherapistAdminOut":
        return cls(
            id=t.id, display_name=t.display_name, short_bio=t.short_bio,
            short_bio_de=t.short_bio_de, active=t.active,
            service_ids=sorted(s.id for s in t.services),
            hours=[
                HoursOut(weekday=h.weekday, start_time=h.start_time.strftime("%H:%M"),
                         end_time=h.end_time.strftime("%H:%M"))
                for h in sorted(t.working_hours, key=lambda h: (h.weekday, h.start_time))
            ],
        )


class TherapistIn(BaseModel):
    display_name: str = Field(max_length=80)
    short_bio: str | None = Field(default=None, max_length=500)
    short_bio_de: str | None = Field(default=None, max_length=500)
    active: bool = True
    service_ids: list[int] = Field(default_factory=list, max_length=50)


class HoursIn(BaseModel):
    weekday: int
    start_time: time
    end_time: time


class HoursListIn(BaseModel):
    hours: list[HoursIn] = Field(max_length=21)


class DayOffIn(BaseModel):
    therapist_id: int | None = None
    date: date
    reason: str | None = Field(default=None, max_length=120)


class DayOffOut(BaseModel):
    id: int
    therapist_id: int | None
    therapist_name: str | None
    date: date
    reason: str | None


# ---------- Slice 5: waitlist ----------


class WaitlistIn(BaseModel):
    service_ids: list[int] = Field(min_length=1, max_length=10)
    add_on_ids: list[int] = Field(default_factory=list, max_length=20)
    therapist_id: int | None = None
    therapist_choices: dict[int, int | None] | None = Field(default=None, max_length=10)
    preferred_date: date
    earliest_time: time
    latest_time: time
    first_name: str = Field(max_length=80)
    last_name: str = Field(max_length=80)
    email: str = Field(max_length=255)
    phone: str = Field(max_length=40)


class WaitlistJoinOut(BaseModel):
    """Identical whether the person was added or already waiting, so the API can't be
    used to find out who is on the waitlist. The position is emailed instead."""

    status: str  # always "received"
    preferred_date: date


class WaitlistConfirmOut(BaseModel):
    status: str
    preferred_date: date
    position: int | None


class OfferLineOut(BaseModel):
    name: str
    price: MoneyStr


class OfferOut(BaseModel):
    """Shown to whoever holds the offer link: the slot, not the customer's details."""

    status: str  # open | claimed | expired
    date: date
    time: str
    therapist_name: str
    total_minutes: int
    total_price: MoneyStr
    lines: list[OfferLineOut]
    visit: list[PlanLineOut] = Field(default_factory=list)
    expires_at: datetime


class OwnerWaitlistOut(BaseModel):
    id: int
    customer_name: str
    email: str
    phone: str
    services: list[str]
    preferred_date: date
    earliest_time: str
    latest_time: str
    therapist_name: str | None
    joined_at: datetime
    status: str
    offered_at: datetime | None
    offer_expires_at: datetime | None
    offer_time: str | None
    booking_id: int | None


# ---------- Treatment photos ----------


class PhotoTexts(BaseModel):
    alt_text: str | None = Field(default=None, max_length=300)
    alt_text_de: str | None = Field(default=None, max_length=300)


class PhotoSettings(BaseModel):
    show_photos: bool


# ---------- Studio settings ----------


class StudioSettings(ORMModel):
    name: str = Field(max_length=120)
    address: str = Field(max_length=255)
    phone: str = Field(max_length=40)
    email: str = Field(max_length=255)
    opening_hours_text: str = Field(default="", max_length=255)
    opening_hours_text_de: str | None = Field(default=None, max_length=255)
    min_notice_hours: int
    free_cancellation_hours: int
    booking_window_days: int
    waitlist_offer_minutes: int
    receipt_prefix: str = Field(max_length=10)
    vat_mode: str = Field(default="19", max_length=20)
    tax_number: str | None = Field(default=None, max_length=60)
