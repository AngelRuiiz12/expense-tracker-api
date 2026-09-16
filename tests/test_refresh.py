from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
CREDENTIALS = {"email": "ana@test.com", "password": "secreta123"}
FORM = {"username": "ana@test.com", "password": "secreta123"}


def _login(client: TestClient) -> dict[str, str]:
    client.post(REGISTER, json=CREDENTIALS)

    return client.post(LOGIN, data=FORM).json()


def test_login_devuelve_los_dos_tokens(client: TestClient) -> None:
    body = _login(client)

    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"].lower() == "bearer"


def test_refresh_devuelve_un_par_nuevo(client: TestClient) -> None:
    inicial = _login(client)

    response = client.post(REFRESH, json={"refresh_token": inicial["refresh_token"]})

    assert response.status_code == 200

    nuevo = response.json()
    assert nuevo["refresh_token"] != inicial["refresh_token"]


def test_el_refresh_token_usado_deja_de_valer(client: TestClient) -> None:
    inicial = _login(client)
    client.post(REFRESH, json={"refresh_token": inicial["refresh_token"]})

    response = client.post(REFRESH, json={"refresh_token": inicial["refresh_token"]})

    assert response.status_code == 401


def test_el_access_token_nuevo_funciona(client: TestClient) -> None:
    inicial = _login(client)
    nuevo = client.post(
        REFRESH, json={"refresh_token": inicial["refresh_token"]}
    ).json()

    response = client.get(
        "/api/v1/categories/",
        headers={"Authorization": f"Bearer {nuevo['access_token']}"},
    )

    assert response.status_code == 200


def test_reutilizar_un_token_revocado_invalida_toda_la_cadena(
    client: TestClient,
) -> None:
    inicial = _login(client)
    segundo = client.post(
        REFRESH, json={"refresh_token": inicial["refresh_token"]}
    ).json()

    robado = client.post(REFRESH, json={"refresh_token": inicial["refresh_token"]})
    legitimo = client.post(REFRESH, json={"refresh_token": segundo["refresh_token"]})

    assert robado.status_code == 401
    assert legitimo.status_code == 401


def test_refresh_token_inventado_devuelve_401(client: TestClient) -> None:
    _login(client)

    response = client.post(REFRESH, json={"refresh_token": "no-existo"})

    assert response.status_code == 401


def test_logout_invalida_el_refresh_token(client: TestClient) -> None:
    inicial = _login(client)

    salida = client.post(LOGOUT, json={"refresh_token": inicial["refresh_token"]})
    response = client.post(REFRESH, json={"refresh_token": inicial["refresh_token"]})

    assert salida.status_code == 204
    assert response.status_code == 401


def test_el_refresh_token_no_se_guarda_en_claro(
    client: TestClient, db: Session
) -> None:
    inicial = _login(client)

    guardado = db.execute(select(RefreshToken)).scalar_one()

    assert guardado.token_hash != inicial["refresh_token"]
    assert len(guardado.token_hash) == 64
