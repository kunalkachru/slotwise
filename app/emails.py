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

from app import i18n
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
#
# Every email is written in the language the customer used (booking.language /
# entry.language), English by default. Dates and prices come from app.i18n.

STRINGS = {
    "en": {
        "with": "with", "total": "Total", "pay": "Pay at the studio.", "paid": "Paid at the studio.",
        "hello": "Hello {name}",
        "confirmed_intro": "{hello}, your booking at {studio} is confirmed.",
        "confirmed_subject": "Booking confirmed: {when} · {studio}",
        "confirmed_heading": "You're booked!",
        "manage": "View or manage your booking",
        "free_until": "Free cancellation until {deadline}.",
        "reminder_intro": ("{hello}, a reminder of your appointment on {when}. Please confirm "
                           "you're coming, or cancel so someone on the waitlist can have the time."),
        "reminder_subject": "Reminder: {when} · {studio}",
        "reminder_heading": "See you soon",
        "coming": "Confirm I'm coming", "cancel": "I need to cancel",
        "receipt_intro": "{hello}, thank you for your visit to {studio}. Here is your receipt {number}.",
        "receipt_subject": "Receipt {number} · {studio}",
        "receipt_heading": "Receipt {number}",
        "receipt_link": "View or print your receipt",
        "verify_intro": ("{hello}, please confirm your booking at {studio}. We're holding the "
                         "time for you until {until}."),
        "verify_subject": "Please confirm your booking: {when} · {studio}",
        "verify_heading": "One more step",
        "verify_link": "Confirm my booking",
        "verify_footer": "If you didn't make this booking, ignore this email and the time will be released.",
        "offer_intro": ("{hello}, a time you were waiting for at {studio} is free: {when} with "
                        "{therapist} ({minutes} min)."),
        "offer_detail": "Claim it before {expires}. After that it goes to the next person on the waitlist.",
        "offer_subject": "A time is free: {when} · {studio}",
        "offer_heading": "A time is free for you",
        "offer_link": "Claim this time",
        "joined_intro": "{hello}, you are on the waitlist at {studio} for {day} ({window}), number {position}.",
        "already_intro": ("{hello}, you are already on the waitlist at {studio} for {day} "
                          "({window}), number {position}."),
        "joined_detail": ("If a time frees up, we'll email you a link to claim it; the first person "
                          "to claim gets it. If you didn't ask for this, ignore this email or call us."),
        "joined_subject": "Waitlist for {day} · {studio}",
        "joined_heading": "You're on the waitlist",
        "limit_intro": ("{hello}, we could not add you to the waitlist at {studio} for {day}: this "
                        "email address already has {limit} open waitlist requests."),
        "limit_detail": ("Please call us on {phone} if you want to change them. If you didn't ask "
                         "for any of this, someone may have used your address; call us and we'll "
                         "remove the requests."),
        "limit_subject": "Waitlist request for {day} · {studio}",
        "wl_confirm_intro": ("{hello}, please confirm that you want to join the waitlist at "
                             "{studio} for {day} ({window})."),
        "wl_confirm_detail": ("The request counts once you confirm, and expires after 24 hours. If "
                              "you didn't ask for this, ignore this email."),
        "wl_confirm_subject": "Please confirm: waitlist for {day} · {studio}",
        "wl_confirm_link": "Confirm my waitlist request",
    },
    "de": {
        "with": "bei", "total": "Gesamt", "pay": "Bezahlung im Studio.", "paid": "Im Studio bezahlt.",
        "hello": "Hallo {name}",
        "confirmed_intro": "{hello}, Ihre Buchung bei {studio} ist bestätigt.",
        "confirmed_subject": "Buchung bestätigt: {when} · {studio}",
        "confirmed_heading": "Sie sind gebucht!",
        "manage": "Buchung ansehen oder verwalten",
        "free_until": "Kostenlose Stornierung bis {deadline}.",
        "reminder_intro": ("{hello}, wir erinnern Sie an Ihren Termin am {when}. Bitte bestätigen "
                           "Sie, dass Sie kommen, oder sagen Sie ab, damit jemand von der "
                           "Warteliste den Termin bekommt."),
        "reminder_subject": "Erinnerung: {when} · {studio}",
        "reminder_heading": "Bis bald",
        "coming": "Ich komme", "cancel": "Ich muss absagen",
        "receipt_intro": ("{hello}, vielen Dank für Ihren Besuch bei {studio}. Hier ist Ihre "
                          "Quittung {number}."),
        "receipt_subject": "Quittung {number} · {studio}",
        "receipt_heading": "Quittung {number}",
        "receipt_link": "Quittung ansehen oder drucken",
        "verify_intro": ("{hello}, bitte bestätigen Sie Ihre Buchung bei {studio}. Wir halten "
                         "den Termin bis {until} für Sie frei."),
        "verify_subject": "Bitte bestätigen Sie Ihre Buchung: {when} · {studio}",
        "verify_heading": "Noch ein Schritt",
        "verify_link": "Buchung bestätigen",
        "verify_footer": ("Falls Sie diese Buchung nicht vorgenommen haben, ignorieren Sie diese "
                          "E-Mail; der Termin wird dann wieder freigegeben."),
        "offer_intro": ("{hello}, ein Termin, auf den Sie bei {studio} gewartet haben, ist frei: "
                        "{when} bei {therapist} ({minutes} Min.)."),
        "offer_detail": ("Bitte sichern Sie ihn sich bis {expires}. Danach geht er an die nächste "
                         "Person auf der Warteliste."),
        "offer_subject": "Ein Termin ist frei: {when} · {studio}",
        "offer_heading": "Ein Termin ist für Sie frei",
        "offer_link": "Termin sichern",
        "joined_intro": ("{hello}, Sie stehen bei {studio} auf der Warteliste für {day} "
                         "({window}), Platz {position}."),
        "already_intro": ("{hello}, Sie stehen bereits bei {studio} auf der Warteliste für {day} "
                          "({window}), Platz {position}."),
        "joined_detail": ("Wird ein Termin frei, senden wir Ihnen einen Link; wer zuerst zugreift, "
                          "bekommt ihn. Falls Sie das nicht angefragt haben, ignorieren Sie diese "
                          "E-Mail oder rufen Sie uns an."),
        "joined_subject": "Warteliste für {day} · {studio}",
        "joined_heading": "Sie stehen auf der Warteliste",
        "limit_intro": ("{hello}, wir konnten Sie bei {studio} nicht auf die Warteliste für {day} "
                        "setzen: Diese E-Mail-Adresse hat bereits {limit} offene "
                        "Wartelisten-Anfragen."),
        "limit_detail": ("Bitte rufen Sie uns unter {phone} an, wenn Sie sie ändern möchten. Falls "
                         "Sie nichts davon angefragt haben, hat jemand Ihre Adresse verwendet; "
                         "rufen Sie uns an, dann entfernen wir die Anfragen."),
        "limit_subject": "Wartelisten-Anfrage für {day} · {studio}",
        "wl_confirm_intro": ("{hello}, bitte bestätigen Sie, dass Sie bei {studio} auf die "
                             "Warteliste für {day} ({window}) möchten."),
        "wl_confirm_detail": ("Die Anfrage zählt erst nach Ihrer Bestätigung und verfällt nach 24 "
                              "Stunden. Falls Sie das nicht angefragt haben, ignorieren Sie diese "
                              "E-Mail."),
        "wl_confirm_subject": "Bitte bestätigen: Warteliste für {day} · {studio}",
        "wl_confirm_link": "Wartelisten-Anfrage bestätigen",
    },
}


def _t(lang: str, key: str, **values) -> str:
    return STRINGS[i18n.lang_of(lang)][key].format(**values)


def _hello(lang: str, customer) -> str:
    return _t(lang, "hello", name=customer.first_name)


def _when(booking) -> str:
    return i18n.long_when(booking.start_at.astimezone(BERLIN), booking.language)


def _studio_line(studio) -> str:
    return f"{studio.name} · {studio.address} · {studio.phone}"


def _lines(booking) -> list[tuple[str, str]]:
    rows = []
    for item in booking.items:
        label = item.name_snapshot if item.item_type == "service" else f"+ {item.name_snapshot}"
        if item.quantity > 1:
            label += f" × {item.quantity}"
        rows.append((label, i18n.euro(item.unit_price_snapshot * item.quantity, booking.language)))
    return rows


def _total_minutes(booking) -> int:
    return sum(i.minutes_snapshot * i.quantity for i in booking.items)


def _minutes(booking) -> str:
    unit = "Min." if booking.language == "de" else "min"
    return f"{_total_minutes(booking)} {unit}"


def manage_link(public_url: str, booking, action: str | None = None) -> str:
    link = f"{public_url}/manage.html?token={booking.manage_token}"
    return f"{link}&action={action}" if action else link


def _html_page(heading: str, intro: str, booking, buttons: list[tuple[str, str]],
               footer: str, paid: bool = False) -> str:
    esc = html.escape
    lang = booking.language
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
        f"<p><strong>{esc(_when(booking))}</strong> {_t(lang, 'with')} "
        f"{esc(booking.therapist.display_name)} ({_minutes(booking)})</p>"
        f'<table style="width:100%;border-collapse:collapse">{rows}'
        f'<tr><td style="padding:8px 0;font-weight:700">{_t(lang, "total")}</td>'
        f'<td style="padding:8px 0;font-weight:700;text-align:right">'
        f"{esc(i18n.euro(booking.total_price, lang))}</td></tr></table>"
        f'<p style="color:#5d6b64">{_t(lang, "paid" if paid else "pay")}</p><p>{links}</p>'
        f'<p style="color:#5d6b64;font-size:14px">{esc(footer)}</p></div>'
    )


def _text_body(intro: str, booking, links: list[tuple[str, str]], footer: str,
               paid: bool = False) -> str:
    lang = booking.language
    lines = [intro, "", f"{_when(booking)} {_t(lang, 'with')} {booking.therapist.display_name} "
             f"({_minutes(booking)})", ""]
    lines += [f"{label:<40} {price:>10}" for label, price in _lines(booking)]
    lines += [f"{_t(lang, 'total'):<40} {i18n.euro(booking.total_price, lang):>10}", "",
              _t(lang, "paid" if paid else "pay"), ""]
    lines += [f"{label}: {url}" for label, url in links]
    lines += ["", footer]
    return "\n".join(lines)


def _simple(to: str, subject: str, heading: str | None, paragraphs: list[str], footer: str,
            reply_to: str, button: tuple[str, str] | None = None) -> Email:
    esc = html.escape
    text = "\n\n".join(paragraphs + ([f"{button[0]}: {button[1]}"] if button else []) + [footer])
    link_html = (
        f'<p><a href="{esc(button[1])}" style="display:inline-block;padding:10px 16px;'
        f'border-radius:8px;background:#1F8756;color:#fff;text-decoration:none;'
        f'font-weight:600">{esc(button[0])}</a></p>' if button else ""
    )
    body = "".join(f"<p>{esc(p)}</p>" for p in paragraphs)
    heading_html = f'<h2 style="color:#1F8756">{esc(heading)}</h2>' if heading else ""
    return Email(
        to=to, subject=subject, text=text, reply_to=reply_to,
        html=('<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;'
              f'max-width:520px;color:#1d2a24">{heading_html}{body}{link_html}'
              f'<p style="color:#5d6b64;font-size:14px">{esc(footer)}</p></div>'),
    )


def confirmation_email(booking, studio, public_url: str) -> Email:
    lang = booking.language
    deadline = (booking.start_at - timedelta(hours=studio.free_cancellation_hours)).astimezone(
        BERLIN)
    intro = _t(lang, "confirmed_intro", hello=_hello(lang, booking.customer), studio=studio.name)
    footer = (f"{_t(lang, 'free_until', deadline=i18n.short_when(deadline, lang))} "
              f"{_studio_line(studio)}")
    links = [(_t(lang, "manage"), manage_link(public_url, booking))]
    return Email(
        to=booking.customer.email,
        subject=_t(lang, "confirmed_subject", when=_when(booking), studio=studio.name),
        text=_text_body(intro, booking, links, footer),
        html=_html_page(_t(lang, "confirmed_heading"), intro, booking, links, footer),
        reply_to=studio.email,
    )


def reminder_email(booking, studio, public_url: str) -> Email:
    """Sent 24 hours before (run-jobs) with one-click confirm and cancel."""
    lang = booking.language
    intro = _t(lang, "reminder_intro", hello=_hello(lang, booking.customer), when=_when(booking))
    links = [
        (_t(lang, "coming"), manage_link(public_url, booking, "confirm")),
        (_t(lang, "cancel"), manage_link(public_url, booking, "cancel")),
    ]
    return Email(
        to=booking.customer.email,
        subject=_t(lang, "reminder_subject", when=_when(booking), studio=studio.name),
        text=_text_body(intro, booking, links, _studio_line(studio)),
        html=_html_page(_t(lang, "reminder_heading"), intro, booking, links, _studio_line(studio)),
        reply_to=studio.email,
    )


def receipt_email(booking, studio, public_url: str) -> Email:
    lang = booking.language
    number = booking.receipt_number
    intro = _t(lang, "receipt_intro", hello=_hello(lang, booking.customer), studio=studio.name,
               number=number)
    vat = i18n.vat_line(booking.total_price, studio.vat_mode, lang)
    footer = f"{_t(lang, 'paid')} {vat} {_studio_line(studio)}"
    links = [(_t(lang, "receipt_link"), f"{public_url}/receipt.html?token={booking.manage_token}")]
    return Email(
        to=booking.customer.email,
        subject=_t(lang, "receipt_subject", number=number, studio=studio.name),
        text=_text_body(intro, booking, links, footer, paid=True),
        html=_html_page(_t(lang, "receipt_heading", number=number), intro, booking, links, footer,
                        paid=True),
        reply_to=studio.email,
    )


def booking_verification_email(booking, studio, public_url: str, hold_until) -> Email:
    """First email after an online booking: only a click proves the address is theirs."""
    lang = booking.language
    until = i18n.clock_time(hold_until.astimezone(BERLIN), lang)
    intro = _t(lang, "verify_intro", hello=_hello(lang, booking.customer), studio=studio.name,
               until=until)
    footer = f"{_t(lang, 'verify_footer')} {_studio_line(studio)}"
    links = [(_t(lang, "verify_link"), manage_link(public_url, booking, "verify"))]
    return Email(
        to=booking.customer.email,
        subject=_t(lang, "verify_subject", when=_when(booking), studio=studio.name),
        text=_text_body(intro, booking, links, footer),
        html=_html_page(_t(lang, "verify_heading"), intro, booking, links, footer),
        reply_to=studio.email,
    )


def waitlist_offer_email(entry, studio, public_url: str, start_local, therapist_name: str,
                         minutes: int) -> Email:
    """A freed slot for someone on the waitlist; first come, valid for a short time."""
    lang = entry.language
    when = i18n.short_when(start_local, lang)
    expires = i18n.clock_time(entry.offer_expires_at.astimezone(BERLIN), lang)
    unit = "Min." if lang == "de" else "min"
    intro = _t(lang, "offer_intro", hello=_hello(lang, entry.customer), studio=studio.name,
               when=when, therapist=therapist_name, minutes=minutes).replace(
                   f"({minutes} min)", f"({minutes} {unit})")
    return _simple(
        entry.customer.email, _t(lang, "offer_subject", when=when, studio=studio.name),
        _t(lang, "offer_heading"), [intro, _t(lang, "offer_detail", expires=expires)],
        _studio_line(studio), studio.email,
        button=(_t(lang, "offer_link"), f"{public_url}/offer.html?token={entry.offer_token}"),
    )


def _window(entry) -> str:
    return f"{entry.earliest_time:%H:%M}–{entry.latest_time:%H:%M}"


def waitlist_joined_email(entry, position: int, studio, already: bool) -> Email:
    """Sent to the address that joined, so only its owner learns the queue position."""
    lang = entry.language
    day = i18n.day_month(entry.preferred_date, lang)
    intro = _t(lang, "already_intro" if already else "joined_intro",
               hello=_hello(lang, entry.customer), studio=studio.name, day=day,
               window=_window(entry), position=position)
    return _simple(entry.customer.email, _t(lang, "joined_subject", day=day, studio=studio.name),
                   _t(lang, "joined_heading"), [intro, _t(lang, "joined_detail")],
                   _studio_line(studio), studio.email)


def waitlist_limit_email(customer, day, studio, limit: int, lang: str = "en") -> Email:
    """A join that changed nothing must not fail silently: tell the address owner."""
    when = i18n.day_month(day, lang)
    intro = _t(lang, "limit_intro", hello=_hello(lang, customer), studio=studio.name, day=when,
               limit=limit)
    return _simple(customer.email, _t(lang, "limit_subject", day=when, studio=studio.name), None,
                   [intro, _t(lang, "limit_detail", phone=studio.phone)], _studio_line(studio),
                   studio.email)


def waitlist_confirm_email(entry, studio, public_url: str) -> Email:
    """Double opt-in: the entry only counts once the address owner clicks."""
    lang = entry.language
    day = i18n.day_month(entry.preferred_date, lang)
    intro = _t(lang, "wl_confirm_intro", hello=_hello(lang, entry.customer), studio=studio.name,
               day=day, window=_window(entry))
    return _simple(
        entry.customer.email, _t(lang, "wl_confirm_subject", day=day, studio=studio.name),
        _t(lang, "verify_heading"), [intro, _t(lang, "wl_confirm_detail")],
        _studio_line(studio), studio.email,
        button=(_t(lang, "wl_confirm_link"),
                f"{public_url}/waitlist-confirm.html?token={entry.confirm_token}"),
    )
