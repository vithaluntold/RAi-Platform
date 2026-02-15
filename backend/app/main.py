import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine, Base, SessionLocal
from app.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)

REMINDER_CHECK_INTERVAL_SECONDS = 60


async def _reminder_loop():
    """Periodically process pending reminders.
    All state lives in the DB — safe across restarts."""
    while True:
        try:
            db = SessionLocal()
            try:
                sent = ReminderService.process_pending_reminders(db)
                if sent:
                    logger.info("Reminder scheduler: sent %d reminder(s)", sent)
            finally:
                db.close()
        except Exception:
            logger.exception("Reminder scheduler error")
        await asyncio.sleep(REMINDER_CHECK_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup / shutdown lifecycle."""
    task = asyncio.create_task(_reminder_loop())
    logger.info("Reminder background scheduler started (interval=%ds)", REMINDER_CHECK_INTERVAL_SECONDS)
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Reminder background scheduler stopped")


# Create tables (only for dev; in production, rely on Alembic migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Build CORS origins — include configured origins + Railway auto-generated domains
_cors_origins: list[str] = [origin.rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS]
# Also allow Railway's auto-generated *.up.railway.app domains
import os as _os
for _var in ("RAILWAY_SERVICE_PROUD_ALIGNMENT_URL", "RAILWAY_PUBLIC_DOMAIN"):
    _val = _os.environ.get(_var, "")
    if _val:
        _url = f"https://{_val.rstrip('/')}" if not _val.startswith("http") else _val.rstrip("/")
        if _url not in _cors_origins:
            _cors_origins.append(_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")
