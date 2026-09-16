from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.deps import get_db
from app.db.base import Base
from app.main import app


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    return _register_and_login(client, "ana@test.com")


@pytest.fixture
def other_headers(client: TestClient) -> dict[str, str]:
    return _register_and_login(client, "pepe@test.com")


def _register_and_login(client: TestClient, email: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register", json={"email": email, "password": "secreta123"}
    )
    response = client.post(
        "/api/v1/auth/login", data={"username": email, "password": "secreta123"}
    )
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def category_id(client: TestClient, auth_headers: dict[str, str]) -> int:
    response = client.post(
        "/api/v1/categories/", json={"name": "Comida"}, headers=auth_headers
    )

    return response.json()["id"]
