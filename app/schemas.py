from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

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
