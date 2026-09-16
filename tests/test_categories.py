from fastapi.testclient import TestClient

CATEGORIES = "/api/v1/categories/"


def test_crear_categoria_devuelve_201(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(CATEGORIES, json={"name": "Comida"}, headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["name"] == "Comida"


def test_nombre_repetido_del_mismo_usuario_devuelve_409(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    client.post(CATEGORIES, json={"name": "Comida"}, headers=auth_headers)

    response = client.post(CATEGORIES, json={"name": "Comida"}, headers=auth_headers)

    assert response.status_code == 409


def test_dos_usuarios_pueden_usar_el_mismo_nombre(
    client: TestClient, auth_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    primera = client.post(CATEGORIES, json={"name": "Comida"}, headers=auth_headers)
    segunda = client.post(CATEGORIES, json={"name": "Comida"}, headers=other_headers)

    assert primera.status_code == 201
    assert segunda.status_code == 201
    assert primera.json()["id"] != segunda.json()["id"]


def test_cada_usuario_solo_ve_sus_categorias(
    client: TestClient, auth_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    client.post(CATEGORIES, json={"name": "Comida"}, headers=auth_headers)
    client.post(CATEGORIES, json={"name": "Ocio"}, headers=other_headers)

    de_ana = client.get(CATEGORIES, headers=auth_headers).json()
    de_pepe = client.get(CATEGORIES, headers=other_headers).json()

    assert [c["name"] for c in de_ana] == ["Comida"]
    assert [c["name"] for c in de_pepe] == ["Ocio"]


def test_categoria_ajena_devuelve_404_y_no_403(
    client: TestClient,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
    category_id: int,
) -> None:
    respuestas = [
        client.get(f"{CATEGORIES}{category_id}", headers=other_headers),
        client.patch(
            f"{CATEGORIES}{category_id}", json={"name": "X"}, headers=other_headers
        ),
        client.delete(f"{CATEGORIES}{category_id}", headers=other_headers),
    ]

    assert [r.status_code for r in respuestas] == [404, 404, 404]


def test_no_se_puede_borrar_una_categoria_con_gastos(
    client: TestClient, auth_headers: dict[str, str], category_id: int
) -> None:
    client.post(
        "/api/v1/expenses/",
        json={"amount": "10.00", "category_id": category_id},
        headers=auth_headers,
    )

    response = client.delete(f"{CATEGORIES}{category_id}", headers=auth_headers)

    assert response.status_code == 409
