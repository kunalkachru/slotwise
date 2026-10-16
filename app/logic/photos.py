"""Treatment photos: upload checks, demo images, and the URL customers load."""

from sqlalchemy import select
from sqlalchemy.orm import Session, defer

from app import clock
from app.errors import AppError
from app.logic.catalog import NOT_FOUND
from app.models import Service, ServicePhoto, Studio

MAX_BYTES = 600 * 1024
# Checked by the file's first bytes, not its name. No SVG: it can carry scripts.
SIGNATURES = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
)
# Built-in demo images per demo treatment (static/img/demo/), else the category artwork.
DEMO_BY_NAME = {
    "Relaxation massage": "demo/relaxation",
    "Deep tissue massage": "demo/deep-tissue",
    "Back and neck massage": "demo/back-neck",
    "Classic facial": "demo/classic-facial",
    "Express facial": "demo/express-facial",
    "Foot reflexology": "demo/foot-reflexology",
}
DEMO_BY_CATEGORY = {"Massages": "art/massages", "Facials": "art/facials",
                    "Reflexology": "art/reflexology"}

TOO_BIG = "Please choose a photo under 600 KB."
WRONG_TYPE = "Please choose a JPEG, PNG or WebP photo."


def image_type(data: bytes) -> str | None:
    for signature, content_type in SIGNATURES:
        if data.startswith(signature):
            return content_type
    if len(data) > 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def photo_url(photo: ServicePhoto | None) -> str | None:
    if photo is None:
        return None
    if photo.demo_key:
        return f"/img/{photo.demo_key}.svg"
    if photo.content_type:  # an upload (the bytes themselves aren't loaded for the menu)
        # The version stamp changes on every upload, so browsers may cache each URL forever.
        return f"/public/services/{photo.service_id}/photo?v={int(photo.updated_at.timestamp())}"
    return None


def _service(db: Session, service_id: int) -> Service:
    service = db.get(Service, service_id)
    if service is None:
        raise AppError(404, NOT_FOUND)
    return service


def save_upload(db: Session, service_id: int, data: bytes) -> ServicePhoto:
    _service(db, service_id)
    if len(data) > MAX_BYTES:
        raise AppError(422, TOO_BIG)
    content_type = image_type(data)
    if content_type is None:
        raise AppError(422, WRONG_TYPE)
    photo = db.get(ServicePhoto, service_id) or ServicePhoto(service_id=service_id)
    photo.content_type, photo.data, photo.demo_key = content_type, data, None
    photo.updated_at = clock.now()
    db.add(photo)
    db.commit()
    return photo


def save_texts(db: Session, service_id: int, alt_text: str | None, alt_text_de: str | None):
    photo = db.get(ServicePhoto, service_id)
    if photo is None:
        raise AppError(404, NOT_FOUND)
    photo.alt_text = " ".join((alt_text or "").split())[:200] or None
    photo.alt_text_de = " ".join((alt_text_de or "").split())[:200] or None
    db.commit()
    return photo


def remove(db: Session, service_id: int) -> None:
    photo = db.get(ServicePhoto, service_id)
    if photo is not None:
        db.delete(photo)
        db.commit()


def use_demo_photos(db: Session) -> int:
    """Give every treatment without a photo a built-in demo image. Returns how many."""
    have = set(db.scalars(select(ServicePhoto.service_id)))
    added = 0
    for service in db.scalars(select(Service).order_by(Service.id)):
        if service.id in have:
            continue
        key = DEMO_BY_NAME.get(service.name) or DEMO_BY_CATEGORY.get(service.category)
        if key:
            db.add(ServicePhoto(service_id=service.id, demo_key=key, updated_at=clock.now()))
            added += 1
    db.commit()
    return added


def remove_demo_photos(db: Session) -> int:
    demos = db.scalars(select(ServicePhoto).where(ServicePhoto.demo_key.is_not(None))).all()
    for photo in demos:
        db.delete(photo)
    db.commit()
    return len(demos)


def photos_by_service(db: Session) -> dict[int, ServicePhoto]:
    """Every photo's details without the image bytes (the menu only needs the URLs)."""
    rows = db.scalars(select(ServicePhoto).options(defer(ServicePhoto.data)))
    return {p.service_id: p for p in rows}


def shown(db: Session) -> bool:
    studio = db.scalar(select(Studio).limit(1))
    return bool(studio and studio.show_photos)
