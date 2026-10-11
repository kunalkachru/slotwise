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
OUTSIDE_BOOKING_WINDOW = "Please choose a time between 2 hours and 60 days from now."
DATE_OUT_OF_RANGE = "Please choose a date within the next 60 days."
NO_THERAPIST_FOR_COMBINATION = "No therapist offers this combination. Please remove a service."
CHOOSE_A_SERVICE = "Please choose at least one service."
SERVICE_UNAVAILABLE = "One of the chosen treatments is no longer available. Please refresh."
NOT_AN_OFFERED_TIME = "Please pick one of the offered times."
INVALID_EMAIL = "Please enter a valid email address"
MISSING_PHONE = "Please enter your phone number."
MISSING_FIRST_NAME = "Please enter your first name."
MISSING_LAST_NAME = "Please enter your last name."
NOTE_TOO_LONG = "Please keep the note under 300 characters."

# Manage link (slice 3)
BOOKING_NOT_FOUND = "Booking not found. Please check the link in your email."
CANNOT_CONFIRM = "This booking can no longer be confirmed."
ALREADY_CANCELLED_OR_FINISHED = "This booking is already cancelled or finished."


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
