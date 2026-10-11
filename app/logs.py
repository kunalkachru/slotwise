"""Logging setup that keeps manage/offer tokens out of the logs.

Tokens are secrets (they open a customer's booking), but they appear in request paths
(/public/bookings/<token>, /public/waitlist/offers/<token>) and in email links
(?token=...). A filter rewrites them before any handler writes the record, including
uvicorn's access log (security review, slice 3).
"""

import logging
import re

_PATH_TOKEN = re.compile(r"(/public/(?:bookings|waitlist/offers)/)([A-Za-z0-9_-]{16,})")
_QUERY_TOKEN = re.compile(r"(token=)([A-Za-z0-9_-]{16,})")


def redact(text: str) -> str:
    return _QUERY_TOKEN.sub(r"\1<redacted>", _PATH_TOKEN.sub(r"\1<token>", text))


def mask_email(address: str) -> str:
    local, _, domain = address.partition("@")
    return f"{local[:2]}***@{domain}" if domain else "***"


class RedactTokens(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == "uvicorn.access" and isinstance(record.args, tuple) and len(
            record.args
        ) == 5:
            # uvicorn's AccessFormatter unpacks these five args; rewrite only the path.
            args = list(record.args)
            args[2] = redact(str(args[2]))
            record.args = tuple(args)
        else:
            message = record.getMessage()
            redacted = redact(message)
            if redacted != message:
                record.msg, record.args = redacted, None
        return True


def install_log_redaction() -> None:
    redactor = RedactTokens()
    for name in ("uvicorn.access", "uvicorn.error", "uvicorn"):
        logger = logging.getLogger(name)
        if not any(isinstance(f, RedactTokens) for f in logger.filters):
            logger.addFilter(redactor)
    for handler in logging.getLogger().handlers:
        if not any(isinstance(f, RedactTokens) for f in handler.filters):
            handler.addFilter(redactor)
