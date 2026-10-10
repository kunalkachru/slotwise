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


class AppError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        return JSONResponse({"detail": exc.message}, status_code=exc.status_code)

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
