from fastapi.testclient import TestClient

LOGIN = "api/v1/auth/login"


def test_rate_limit_permite_5_intentos(client: TestClient) -> None:
    credentials = {"username": "inexistente@test.com", "password": "incorrecta"}

    for _ in range(5):
        response = client.post(LOGIN, data=credentials)
        assert response.status_code == 401


def test_rate_limit_bloquea_sexto_intento(client: TestClient) -> None:
    credentials = {"username": "inexistente@test.com", "password": "incorrecta"}

    for _ in range(5):
        client.post(LOGIN, data=credentials)

    response = client.post(LOGIN, data=credentials)  # Sexto intento
    assert response.status_code == 429
    assert "Demasiados intentos" in response.json()["detail"]
