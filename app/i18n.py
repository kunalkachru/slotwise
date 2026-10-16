"""German / English for customer-facing text that comes from the server.

- The page sends `X-Lang: de` (or `en`); anything else means English.
- Error messages stay English in the code (one source of truth) and are translated
  centrally in the error handler, so no raise site has to know about languages.
- Dates are formatted here without relying on the server's OS locale.
"""

import re
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from fastapi import Request

from app.models import LANGUAGES

WEEKDAYS = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "de": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
}
WEEKDAYS_SHORT = {
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "de": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
}
MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
           "September", "Oktober", "November", "Dezember"],
}
MONTHS_SHORT = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "de": ["Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sept.", "Okt.",
           "Nov.", "Dez."],
}


CATEGORY_LABELS_DE = {"Massages": "Massagen", "Facials": "Gesichtsbehandlungen",
                      "Reflexology": "Reflexzonenmassage"}


def category_label(category: str, lang: str) -> str:
    return CATEGORY_LABELS_DE.get(category, category) if lang == "de" else category


def lang_of(value: str | None) -> str:
    return value if value in LANGUAGES else "en"


def request_lang(request: Request) -> str:
    return lang_of((request.headers.get("x-lang") or "").strip().lower())


def long_date(day: date, lang: str) -> str:
    """Tuesday 13 October 2026 / Dienstag, 13. Oktober 2026"""
    return f"{day_month(day, lang)} {day.year}"


def day_month(day: date, lang: str) -> str:
    """Tuesday 13 October / Dienstag, 13. Oktober"""
    if lang == "de":
        return f"{WEEKDAYS['de'][day.weekday()]}, {day.day}. {MONTHS['de'][day.month - 1]}"
    return f"{WEEKDAYS['en'][day.weekday()]} {day.day} {MONTHS['en'][day.month - 1]}"


def long_when(moment: datetime, lang: str) -> str:
    """Tuesday 13 October 2026, 10:00 / Dienstag, 13. Oktober 2026, 10:00 Uhr"""
    suffix = " Uhr" if lang == "de" else ""
    return f"{long_date(moment.date(), lang)}, {moment:%H:%M}{suffix}"


def short_when(moment: datetime, lang: str) -> str:
    """Tue 13 Oct, 10:00 / Di., 13. Okt., 10:00 Uhr"""
    if lang == "de":
        return (f"{WEEKDAYS_SHORT['de'][moment.weekday()]}., {moment.day}. "
                f"{MONTHS_SHORT['de'][moment.month - 1]}, {moment:%H:%M} Uhr")
    return (f"{WEEKDAYS_SHORT['en'][moment.weekday()]} {moment.day} "
            f"{MONTHS_SHORT['en'][moment.month - 1]}, {moment:%H:%M}")


def clock_time(moment: datetime, lang: str) -> str:
    return f"{moment:%H:%M} Uhr" if lang == "de" else f"{moment:%H:%M}"


def euro(amount, lang: str) -> str:
    """€82.00 / 82,00 €"""
    if lang == "de":
        return f"{amount:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€{amount:,.2f}"


# ---------- VAT on receipts ----------

VAT_MODES = ("19", "7", "small_business")
# Above this gross amount a receipt is no longer a Kleinbetragsrechnung (§33 UStDV): a full
# invoice then also needs the customer's name and address and the VAT amount (§14 UStG).
SMALL_RECEIPT_LIMIT = Decimal("250.00")


def vat_included(total: Decimal, mode: str) -> Decimal | None:
    """The VAT contained in a gross total, rounded to the cent; None when no VAT is charged."""
    if mode not in ("19", "7"):
        return None
    rate = Decimal(mode)
    return (total * rate / (100 + rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def vat_line(total: Decimal, mode: str, lang: str) -> str:
    """incl. 19% VAT: €13.09 / inkl. 19 % MwSt.: 13,09 € / the §19 UStG note."""
    amount = vat_included(total, mode)
    if amount is None:
        return ("Gemäß § 19 UStG wird keine Umsatzsteuer berechnet." if lang == "de"
                else "No VAT is charged: small business under § 19 UStG.")
    if lang == "de":
        return f"inkl. {mode} % MwSt.: {euro(amount, lang)}"
    return f"incl. {mode}% VAT: {euro(amount, lang)}"


# ---------- Server messages ----------

MESSAGES_DE = {
    "Something went wrong. Please try again.":
        "Etwas ist schiefgelaufen. Bitte versuchen Sie es erneut.",
    "Please check the highlighted fields.": "Bitte prüfen Sie die markierten Felder.",
    "Email or password is wrong.": "E-Mail-Adresse oder Passwort ist falsch.",
    "Too many attempts. Try again in 5 minutes.":
        "Zu viele Versuche. Bitte versuchen Sie es in 5 Minuten erneut.",
    "Please log in.": "Bitte melden Sie sich an.",
    "That time was just taken. Please pick another.":
        "Diese Zeit wurde gerade vergeben. Bitte wählen Sie eine andere.",
    "No therapist offers this combination. Please remove a service.":
        "Keine Therapeutin bietet diese Kombination an. Bitte entfernen Sie eine Behandlung.",
    "Please choose at least one service.": "Bitte wählen Sie mindestens eine Behandlung.",
    "One of the chosen treatments is no longer available. Please refresh.":
        "Eine der gewählten Behandlungen ist nicht mehr verfügbar. Bitte laden Sie die Seite neu.",
    "Please pick one of the offered times.": "Bitte wählen Sie eine der angebotenen Zeiten.",
    "Please enter a valid email address": "Bitte geben Sie eine gültige E-Mail-Adresse ein.",
    "Please enter your phone number.": "Bitte geben Sie Ihre Telefonnummer ein.",
    "Please enter your first name.": "Bitte geben Sie Ihren Vornamen ein.",
    "Please enter your last name.": "Bitte geben Sie Ihren Nachnamen ein.",
    "Please keep the note under 300 characters.":
        "Bitte halten Sie die Notiz unter 300 Zeichen.",
    "Please use only letters in your name.": "Bitte verwenden Sie nur Buchstaben im Namen.",
    "Too many bookings in a short time. Please call the studio.":
        "Zu viele Buchungen in kurzer Zeit. Bitte rufen Sie das Studio an.",
    "Booking not found. Please check the link in your email.":
        "Buchung nicht gefunden. Bitte prüfen Sie den Link in Ihrer E-Mail.",
    "This booking can no longer be confirmed.":
        "Diese Buchung kann nicht mehr bestätigt werden.",
    "This booking is already cancelled or finished.":
        "Diese Buchung ist bereits storniert oder abgeschlossen.",
    "This booking request has expired because it wasn't confirmed in time. Please book again.":
        "Diese Buchungsanfrage ist abgelaufen, weil sie nicht rechtzeitig bestätigt wurde. "
        "Bitte buchen Sie erneut.",
    "This waitlist request has expired because it wasn't confirmed in time. Please join again.":
        "Diese Wartelisten-Anfrage ist abgelaufen, weil sie nicht rechtzeitig bestätigt wurde. "
        "Bitte tragen Sie sich erneut ein.",
    "Waitlist request not found. Please check the link in your email.":
        "Wartelisten-Anfrage nicht gefunden. Bitte prüfen Sie den Link in Ihrer E-Mail.",
    "You already have 5 open waitlist requests. Please call the studio to change them.":
        "Sie haben bereits 5 offene Wartelisten-Anfragen. Bitte rufen Sie das Studio an, um sie "
        "zu ändern.",
    "Offer not found.": "Angebot nicht gefunden.",
    "Sorry, this offer has expired.": "Leider ist dieses Angebot abgelaufen.",
    "This offer was already claimed.": "Dieses Angebot wurde bereits angenommen.",
    "Please choose an earliest time before the latest time.":
        "Bitte wählen Sie eine früheste Zeit vor der spätesten Zeit.",
    "Nobody offers this treatment on that day, so no time can free up.":
        "An diesem Tag bietet niemand diese Behandlung an, daher kann keine Zeit frei werden.",
    "The studio is not set up yet.": "Das Studio ist noch nicht eingerichtet.",
}

_DYNAMIC_DE = [
    (re.compile(r"^Please choose a time between (\d+) hours? and (\d+) days from now\.$"),
     lambda m: f"Bitte wählen Sie eine Zeit zwischen {m[1]} "
               f"{'Stunde' if m[1] == '1' else 'Stunden'} und {m[2]} Tagen ab jetzt."),
    (re.compile(r"^Please choose a date within the next (\d+) days\.$"),
     lambda m: f"Bitte wählen Sie ein Datum innerhalb der nächsten {m[1]} Tage."),
]


def translate(message: str, lang: str) -> str:
    if lang != "de":
        return message
    if message in MESSAGES_DE:
        return MESSAGES_DE[message]
    for pattern, render in _DYNAMIC_DE:
        match = pattern.match(message)
        if match:
            return render(match)
    return message
