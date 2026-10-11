from datetime import date, datetime
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


class CategoryOut(BaseModel):
    name: str
    services: list[ServiceOut]


class LoginIn(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=200)


class OwnerOut(ORMModel):
    id: int
    full_name: str
    email: str


class DashboardOut(BaseModel):
    date: str
    owner_name: str


# ---------- Slice 2: availability and booking ----------


class TherapistOut(ORMModel):
    id: int
    display_name: str
    short_bio: str | None


class SlotOut(BaseModel):
    time: str  # "17:00", Europe/Berlin
    start_at: datetime
    therapist_id: int
    therapist_name: str


class AvailabilityOut(BaseModel):
    date: date
    total_minutes: int
    slots: list[SlotOut]


class BookingIn(BaseModel):
    service_ids: list[int] = Field(min_length=1, max_length=10)
    add_on_ids: list[int] = Field(default_factory=list, max_length=20)
    therapist_id: int | None = None
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


class BookingOut(BaseModel):
    id: int
    manage_token: str
    status: str
    source: str
    start_at: datetime
    end_at: datetime
    date: date
    time: str
    total_minutes: int
    total_price: MoneyStr
    therapist_name: str
    customer_first_name: str
    items: list[BookingItemOut]

    @classmethod
    def from_booking(cls, booking, first_name: str) -> "BookingOut":
        """`first_name` is the name submitted with this booking. Never echo the saved
        customer's name: the booker may not be that customer (security review)."""
        local_start = booking.start_at.astimezone(BERLIN)
        return cls(
            id=booking.id,
            manage_token=booking.manage_token,
            status=booking.status,
            source=booking.source,
            start_at=booking.start_at,
            end_at=booking.end_at,
            date=local_start.date(),
            time=local_start.strftime("%H:%M"),
            total_minutes=sum(i.minutes_snapshot * i.quantity for i in booking.items),
            total_price=booking.total_price,
            therapist_name=booking.therapist.display_name,
            customer_first_name=first_name,
            items=[
                BookingItemOut(
                    item_type=i.item_type,
                    name=i.name_snapshot,
                    minutes=i.minutes_snapshot,
                    unit_price=i.unit_price_snapshot,
                    quantity=i.quantity,
                    line_total=i.unit_price_snapshot * i.quantity,
                )
                for i in booking.items
            ],
        )
