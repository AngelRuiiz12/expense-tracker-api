import logging

from apscheduler.schedulers.background import BackgroundScheduler

import app.crud.refresh_token as refresh_crud
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def purge_expired_tokens() -> None:
    with SessionLocal() as db:
        borrados = refresh_crud.delete_expired(db)

    logger.info("Refresh tokens caducados borrados: %d", borrados)


def start_scheduler() -> None:
    scheduler.add_job(
        purge_expired_tokens,
        "interval",
        hours=1,
        id="purge_expired_tokens",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
