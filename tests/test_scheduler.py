import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.scheduler import scheduler
from app.main import app


def test_el_scheduler_arranca_y_se_para_con_la_app(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "scheduler_enabled", True)

    with TestClient(app):
        assert scheduler.running
        assert scheduler.get_job("purge_expired_tokens") is not None

    assert not scheduler.running


def test_con_el_interruptor_apagado_la_app_no_arranca_el_scheduler() -> None:
    with TestClient(app):
        assert not scheduler.running
