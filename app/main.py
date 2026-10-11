import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import Settings
from app.db import Base, make_engine, make_session_factory
from app.emails import Mailer
from app.errors import install_error_handlers
from app.logs import install_log_redaction
from app.routers import auth, health, internal, owner, public
from app.security import LoginLimiter, RateLimiter
from app.seed import seed

STATIC_DIR = Path(__file__).parent / "static"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. The database is only touched at startup, so importing is side-effect free."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        cfg = settings or Settings.from_env()
        engine = make_engine(cfg.database_url)
        Base.metadata.create_all(engine)
        app.state.settings = cfg
        app.state.engine = engine
        app.state.session_factory = make_session_factory(engine)
        app.state.login_limiter = LoginLimiter()
        app.state.mailer = Mailer(cfg.email_api_key, cfg.email_from)
        app.state.booking_limiter = RateLimiter()
        install_log_redaction()
        with app.state.session_factory() as db:
            seed(db, cfg)
        yield
        engine.dispose()

    app = FastAPI(title="Slotwise", lifespan=lifespan, docs_url="/api/docs", redoc_url=None)
    install_error_handlers(app)
    for module in (health, public, auth, owner, internal):
        app.include_router(module.router)
    # Mounted last so API routes win; html=True serves index.html for "/".
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


app = create_app()
