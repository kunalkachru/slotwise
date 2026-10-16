"""An .ics file for one booking, so customers can add it to their phone's calendar."""

from datetime import UTC, datetime

from app import clock


def _escape(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
            .replace("\r\n", "\\n").replace("\n", "\\n"))


def _fold(line: str) -> str:
    """RFC 5545: lines longer than 75 octets continue on the next line after a space."""
    out, current = [], ""
    for char in line:
        if len((current + char).encode()) > 75:
            out.append(current)
            current = " " + char
        else:
            current += char
    return "\r\n".join([*out, current])


def _utc(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _who(booking) -> str:
    """"Lena", or with several therapists one line per part: "10:00 Deep tissue massage —
    Lena". The event itself spans the whole visit."""
    if not booking.has_several_therapists:
        return booking.therapist.display_name
    return "\n".join(
        f"{line.start_at.astimezone(clock.BERLIN):%H:%M} {' '.join(line.names)} — "
        f"{line.therapist_name}" for line in booking.visit_plan() if not line.is_break)


def booking_ics(booking, studio, manage_url: str) -> str:
    treatments = ", ".join(i.name_snapshot for i in booking.items if i.item_type == "service")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Slotwise//Booking//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:booking-{booking.id}@slotwise",
        f"DTSTAMP:{_utc(clock.now())}",
        f"DTSTART:{_utc(booking.start_at)}",
        f"DTEND:{_utc(booking.end_at)}",
        f"SUMMARY:{_escape(f'{treatments} · {studio.name}')}",
        f"LOCATION:{_escape(studio.address)}",
        f"DESCRIPTION:{_escape(f'{_who(booking)} · {manage_url}')}",
        f"URL:{manage_url}",
        "STATUS:" + ("CANCELLED" if booking.status in ("cancelled", "expired") else "CONFIRMED"),
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"
