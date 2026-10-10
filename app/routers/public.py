from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.errors import AppError
from app.models import CATEGORIES, Service, Studio
from app.schemas import AddOnOut, CategoryOut, ServiceOut, StudioOut

router = APIRouter(prefix="/public", tags=["public"])


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
