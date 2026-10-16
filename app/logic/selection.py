"""What the customer picked: services + add-ons, resolved against the live menu."""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.errors import (
    CHOOSE_A_SERVICE,
    NO_THERAPIST_FOR_COMBINATION,
    SERVICE_UNAVAILABLE,
    AppError,
)
from app.models import AddOn, BookingItem, Service, Therapist


def localized(english: str | None, german: str | None, lang: str) -> str | None:
    """The German text when asked for and filled in; otherwise the English one."""
    return german if lang == "de" and german else english


@dataclass(frozen=True)
class Selection:
    services: list[Service]
    add_ons: list[AddOn]

    @property
    def service_ids(self) -> list[int]:
        return [s.id for s in self.services]

    @property
    def total_minutes(self) -> int:
        return sum(s.duration_minutes for s in self.services) + sum(
            a.extra_minutes for a in self.add_ons
        )

    def step_minutes(self, service: Service) -> int:
        """One treatment with its own add-ons: how long that part of the visit takes."""
        return service.duration_minutes + sum(
            a.extra_minutes for a in self.add_ons if a.service_id == service.id
        )

    @property
    def buffer_minutes(self) -> int:
        """Cleanup after the appointment: the largest buffer of the chosen services."""
        return max(s.buffer_minutes for s in self.services)

    @property
    def blocked_minutes(self) -> int:
        return self.total_minutes + self.buffer_minutes

    @property
    def total_price(self) -> Decimal:
        return sum((i.unit_price_snapshot * i.quantity for i in self.snapshot_items()), Decimal(0))

    def snapshot_items(self, lang: str = "en") -> list[BookingItem]:
        """Booking lines that copy today's name, minutes and price (PLAN.md: price snapshot).
        Names are copied in the language the customer booked in (English fallback)."""
        items = [
            BookingItem(item_type="service", service_id=s.id,
                        name_snapshot=localized(s.name, s.name_de, lang),
                        minutes_snapshot=s.duration_minutes, unit_price_snapshot=s.price,
                        quantity=1)
            for s in self.services
        ]
        items += [
            BookingItem(item_type="add_on", add_on_id=a.id,
                        name_snapshot=localized(a.name, a.name_de, lang),
                        minutes_snapshot=a.extra_minutes, unit_price_snapshot=a.price,
                        quantity=1)
            for a in self.add_ons
        ]
        return items


def parse_ids(raw: str | None) -> list[int]:
    """'1,2, 3' -> [1, 2, 3]; duplicates removed, order kept."""
    if not raw:
        return []
    ids: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise AppError(422, SERVICE_UNAVAILABLE)
        if int(part) not in ids:
            ids.append(int(part))
    return ids


def resolve_selection(db: Session, service_ids: list[int], add_on_ids: list[int]) -> Selection:
    # Each service and add-on counts once, however often a client repeats its id.
    service_ids = list(dict.fromkeys(service_ids))
    add_on_ids = list(dict.fromkeys(add_on_ids))
    if not service_ids:
        raise AppError(422, CHOOSE_A_SERVICE, field="service_ids")
    services = db.scalars(
        select(Service).where(Service.id.in_(service_ids), Service.active.is_(True))
    ).all()
    if len(services) != len(service_ids):
        raise AppError(422, SERVICE_UNAVAILABLE, field="service_ids")

    add_ons: list[AddOn] = []
    if add_on_ids:
        add_ons = list(
            db.scalars(select(AddOn).where(AddOn.id.in_(add_on_ids), AddOn.active.is_(True))).all()
        )
        chosen = set(service_ids)
        if len(add_ons) != len(add_on_ids) or any(a.service_id not in chosen for a in add_ons):
            raise AppError(422, SERVICE_UNAVAILABLE, field="add_on_ids")

    by_id = {s.id: s for s in services}
    add_ons.sort(key=lambda a: add_on_ids.index(a.id))
    return Selection(services=[by_id[i] for i in service_ids], add_ons=add_ons)


def qualified_therapists(db: Session, selection: Selection) -> list[Therapist]:
    """Active therapists who offer every chosen service, lowest id first."""
    therapists = db.scalars(
        select(Therapist)
        .where(Therapist.active.is_(True))
        .options(selectinload(Therapist.services), selectinload(Therapist.working_hours))
        .order_by(Therapist.id)
    ).all()
    wanted = set(selection.service_ids)
    return [t for t in therapists if wanted <= {s.id for s in t.services}]


def therapist_candidates(
    db: Session, selection: Selection, therapist_id: int | None = None,
    choices: dict[int, int | None] | None = None,
) -> dict[int, list[Therapist]]:
    """Per chosen treatment: who may do it, lowest id first (option B: one therapist per
    segment). `therapist_id` (the old API) means that therapist does every treatment;
    `choices` maps a service id to a therapist id, or None for "No preference".
    A chosen therapist who doesn't offer the treatment leaves no one, so no times."""
    therapists = db.scalars(
        select(Therapist)
        .where(Therapist.active.is_(True))
        .options(selectinload(Therapist.services), selectinload(Therapist.working_hours))
        .order_by(Therapist.id)
    ).all()
    result: dict[int, list[Therapist]] = {}
    for service in selection.services:
        offering = [t for t in therapists if service.id in {s.id for s in t.services}]
        if not offering:
            raise AppError(404, NO_THERAPIST_FOR_COMBINATION)
        wanted = therapist_id if therapist_id is not None else (choices or {}).get(service.id)
        result[service.id] = [t for t in offering if wanted is None or t.id == wanted]
    return result


def parse_choices(raw: str | None) -> dict[int, int | None]:
    """'3:1,5:any' -> {3: 1, 5: None} (service id: therapist id, or no preference)."""
    choices: dict[int, int | None] = {}
    for part in (raw or "").split(","):
        if not part.strip():
            continue
        service, _, therapist = part.strip().partition(":")
        therapist = therapist.strip()
        if not service.strip().isdigit() or not (therapist in ("", "any") or therapist.isdigit()):
            raise AppError(422, SERVICE_UNAVAILABLE)
        choices[int(service)] = int(therapist) if therapist.isdigit() else None
    return choices


def require_therapists(db: Session, selection: Selection) -> list[Therapist]:
    therapists = qualified_therapists(db, selection)
    if not therapists:
        raise AppError(404, NO_THERAPIST_FOR_COMBINATION)
    return therapists
