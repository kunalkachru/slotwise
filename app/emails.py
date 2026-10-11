"""All email goes through Mailer.send() (one place, as the blueprint asks).

Without EMAIL_API_KEY the message is printed to the log. With it, it is sent through
Resend's HTTP API using only the standard library. A failed send is logged and never
breaks the action that triggered it (a booking must not fail because email is down).
"""

import html
import json
import logging
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass
from datetime import timedelta

from app.clock import BERLIN
from app.logs import mask_email, redact

log = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


@dataclass(frozen=True)
class Email:
    to: str
    subject: str
    text: str
    html: str
    reply_to: str | None = None


class Mailer:
    def __init__(self, api_key: str | None, sender: str):
        self.api_key = api_key
        self.sender = sender
        self.outbox: deque[Email] = deque(maxlen=50)  # last messages, for tests and debugging

    def send(self, email: Email) -> bool:
        self.outbox.append(email)
        if not self.api_key:
            # Log mode: masked recipient and no secret links (security review, slice 3).
            log.info("EMAIL (log only, not sent) to=%s subject=%s\n%s",
                     mask_email(email.to), email.subject, redact(email.text))
            return True
        payload = {
            "from": self.sender,
            "to": [email.to],
            "subject": email.subject,
            "text": email.text,
            "html": email.html,
        }
        if email.reply_to:
            payload["reply_to"] = email.reply_to
        request = urllib.request.Request(
            RESEND_URL,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "slotwise",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return 200 <= response.status < 300
        except (urllib.error.URLError, TimeoutError, OSError):
            log.exception("Could not send email '%s' to %s", email.subject, mask_email(email.to))
            return False


# ---------- Message builders ----------


def _euro(amount) -> str:
    return f"€{amount:.2f}"


def _when(booking) -> str:
    local = booking.start_at.astimezone(BERLIN)
    return local.strftime("%A %-d %B %Y, %H:%M")


def _lines(booking) -> list[tuple[str, str]]:
    rows = []
    for item in booking.items:
        label = item.name_snapshot if item.item_type == "service" else f"+ {item.name_snapshot}"
        if item.quantity > 1:
            label += f" × {item.quantity}"
        rows.append((label, _euro(item.unit_price_snapshot * item.quantity)))
    return rows


def _total_minutes(booking) -> int:
    return sum(i.minutes_snapshot * i.quantity for i in booking.items)


def manage_link(public_url: str, booking, action: str | None = None) -> str:
    link = f"{public_url}/manage.html?token={booking.manage_token}"
    return f"{link}&action={action}" if action else link


def _html_page(heading: str, intro: str, booking, buttons: list[tuple[str, str]],
               footer: str) -> str:
    esc = html.escape
    rows = "".join(
        f'<tr><td style="padding:6px 0;border-bottom:1px solid #e3e9e5">{esc(label)}</td>'
        f'<td style="padding:6px 0;border-bottom:1px solid #e3e9e5;text-align:right">'
        f"{esc(price)}</td></tr>"
        for label, price in _lines(booking)
    )
    links = "".join(
        f'<a href="{esc(url)}" style="display:inline-block;margin:4px 8px 4px 0;'
        f"padding:10px 16px;border-radius:8px;background:#1F8756;color:#fff;"
        f'text-decoration:none;font-weight:600">{esc(label)}</a>'
        for label, url in buttons
    )
    return (
        '<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;'
        'max-width:520px;color:#1d2a24">'
        f'<h2 style="color:#1F8756">{esc(heading)}</h2><p>{esc(intro)}</p>'
        f"<p><strong>{esc(_when(booking))}</strong> with "
        f"{esc(booking.therapist.display_name)} ({_total_minutes(booking)} min)</p>"
        f'<table style="width:100%;border-collapse:collapse">{rows}'
        f'<tr><td style="padding:8px 0;font-weight:700">Total</td>'
        f'<td style="padding:8px 0;font-weight:700;text-align:right">'
        f"{esc(_euro(booking.total_price))}</td></tr></table>"
        f'<p style="color:#5d6b64">Pay at the studio.</p><p>{links}</p>'
        f'<p style="color:#5d6b64;font-size:14px">{esc(footer)}</p></div>'
    )


def _text_body(intro: str, booking, links: list[tuple[str, str]], footer: str) -> str:
    lines = [intro, "", f"{_when(booking)} with {booking.therapist.display_name} "
             f"({_total_minutes(booking)} min)", ""]
    lines += [f"{label:<40} {price:>10}" for label, price in _lines(booking)]
    lines += [f"{'Total':<40} {_euro(booking.total_price):>10}", "", "Pay at the studio.", ""]
    lines += [f"{label}: {url}" for label, url in links]
    lines += ["", footer]
    return "\n".join(lines)


def confirmation_email(booking, studio, public_url: str) -> Email:
    deadline = (booking.start_at - timedelta(hours=studio.free_cancellation_hours)).astimezone(
        BERLIN
    )
    intro = f"Hello {booking.customer.first_name}, your booking at {studio.name} is confirmed."
    footer = (
        f"Free cancellation until {deadline.strftime('%a %-d %b, %H:%M')}. "
        f"{studio.name} · {studio.address} · {studio.phone}"
    )
    links = [("View or manage your booking", manage_link(public_url, booking))]
    return Email(
        to=booking.customer.email,
        subject=f"Booking confirmed: {_when(booking)} · {studio.name}",
        text=_text_body(intro, booking, links, footer),
        html=_html_page("You're booked!", intro, booking, links, footer),
        reply_to=studio.email,
    )


def reminder_email(booking, studio, public_url: str) -> Email:
    """Sent 24 hours before (slice 5 schedules it) with one-click confirm and cancel."""
    intro = f"Hello {booking.customer.first_name}, a reminder of your appointment tomorrow."
    footer = f"{studio.name} · {studio.address} · {studio.phone}"
    links = [
        ("Confirm I'm coming", manage_link(public_url, booking, "confirm")),
        ("I need to cancel", manage_link(public_url, booking, "cancel")),
    ]
    return Email(
        to=booking.customer.email,
        subject=f"Reminder: {_when(booking)} · {studio.name}",
        text=_text_body(intro, booking, links, footer),
        html=_html_page("See you tomorrow", intro, booking, links, footer),
        reply_to=studio.email,
    )
