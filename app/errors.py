"""One error shape for the whole API: {"detail": "<message shown to the user>"}.

Messages come verbatim from the blueprint (answers.back_end_error_situations_and_messages).
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)

UNEXPECTED = "Something went wrong. Please try again."
WRONG_LOGIN = "Email or password is wrong."
TOO_MANY_ATTEMPTS = "Too many attempts. Try again in 5 minutes."
NOT_LOGGED_IN = "Please log in."

# Booking (slice 2)
TIME_TAKEN = "That time was just taken. Please pick another."


def outside_booking_window(min_notice_hours: int, window_days: int) -> str:
    # Blueprint wording; with the default rules: "between 2 hours and 60 days".
    hours = f"{min_notice_hours} hour{'s' if min_notice_hours != 1 else ''}"
    return f"Please choose a time between {hours} and {window_days} days from now."


def date_out_of_range(window_days: int) -> str:
    return f"Please choose a date within the next {window_days} days."
NO_THERAPIST_FOR_COMBINATION = "No therapist offers this combination. Please remove a service."
CHOOSE_A_SERVICE = "Please choose at least one service."
SERVICE_UNAVAILABLE = "One of the chosen treatments is no longer available. Please refresh."
NOT_AN_OFFERED_TIME = "Please pick one of the offered times."
INVALID_EMAIL = "Please enter a valid email address"
MISSING_PHONE = "Please enter your phone number."
MISSING_FIRST_NAME = "Please enter your first name."
MISSING_LAST_NAME = "Please enter your last name."
NOTE_TOO_LONG = "Please keep the note under 300 characters."
NAME_CHARACTERS = "Please use only letters in your name."
TOO_MANY_BOOKINGS = "Too many bookings in a short time. Please call the studio."

# Waitlist (slice 5)
OFFER_NOT_FOUND = "Offer not found."
OFFER_EXPIRED = "Sorry, this offer has expired."
OFFER_ALREADY_CLAIMED = "This offer was already claimed."
INVALID_TIME_WINDOW = "Please choose an earliest time before the latest time."

# Manage link (slice 3)
BOOKING_NOT_FOUND = "Booking not found. Please check the link in your email."
CANNOT_CONFIRM = "This booking can no longer be confirmed."
ALREADY_CANCELLED_OR_FINISHED = "This booking is already cancelled or finished."
BOOKING_REQUEST_EXPIRED = (
    "This booking request has expired because it wasn't confirmed in time. Please book again."
)
WAITLIST_LIMIT_REACHED = (
    "You already have 5 open waitlist requests. Please call the studio to change them."
)
WAITLIST_REQUEST_EXPIRED = (
    "This waitlist request has expired because it wasn't confirmed in time. Please join again."
)


class AppError(Exception):
    """An error with a user-facing message. `field` lets the page highlight one input."""

    def __init__(self, status_code: int, message: str, field: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.field = field


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        body: dict = {"detail": exc.message}
        if exc.field:
            body["fields"] = [{"field": exc.field, "message": exc.message}]
        return JSONResponse(body, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError):
        fields = [
            {"field": ".".join(str(p) for p in err["loc"][1:]), "message": err["msg"]}
            for err in exc.errors()
        ]
        return JSONResponse(
            {"detail": "Please check the highlighted fields.", "fields": fields},
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception):
        log.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse({"detail": UNEXPECTED}, status_code=500)
