import pytest
from fastapi.testclient import TestClient

REGISTER = "/api/v1/auth/register"
LOGIN = "api/v1/auth/login"
CREDENTIALS = {"email": "ana@test.com", "password": "secreta123"}


def test_register_devuelve_201_sin_contraseña(client: TestClient) -> None:
    response = client.post(REGISTER, json=CREDENTIALS)

    assert response.status_code == 201

    body = response.json()
    assert body["email"] == "ana@test.com"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_con_email_repetido_devuelve_409(client: TestClient) -> None:
    client.post(REGISTER, json=CREDENTIALS)

    response = client.post(REGISTER, json=CREDENTIALS)

    assert response.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "no-es-un-email", "password": "secreta123"},
        {"email": "ana@test.com", "password": "corta"},
        {"email": "ana@test.com"},
    ],
)
def test_register_rechaza_datos_invalidos(
    client: TestClient, payload: dict[str, str]
) -> None:
    response = client.post(REGISTER, json=payload)

    assert response.status_code == 422


def test_login_devuelve_token_bearer(client: TestClient) -> None:
    client.post(REGISTER, json=CREDENTIALS)

    response = client.post(
        LOGIN, data={"username": "ana@test.com", "password": "secreta123"}
    )

    assert response.status_code == 200

    body = response.json()
    assert body["token_type"].lower() == "bearer"
    assert body["access_token"]


def test_login_no_distingue_usuario_de_contraseña(client: TestClient) -> None:
    client.post(REGISTER, json=CREDENTIALS)

    mala_contraseña = client.post(
        LOGIN, data={"username": "ana@test.com", "password": "incorrecta"}
    )
    usuario_inexistente = client.post(
        LOGIN, data={"username": "nadie@test.com", "password": "secreta123"}
    )

    assert mala_contraseña.status_code == 401
    assert usuario_inexistente.status_code == 401
    assert mala_contraseña.json() == usuario_inexistente.json()


@pytest.mark.parametrize(
    "headers",
    [None, {"Authorization": "Bearer inventado"}, {"Authorization": "secreta123"}],
)
def test_endpoints_protegidos_exigen_token(
    client: TestClient, headers: dict[str, str] | None
) -> None:
    response = client.post("/api/v1/categories/", headers=headers)

    assert response.status_code == 401
