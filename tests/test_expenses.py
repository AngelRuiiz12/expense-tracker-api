from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

EXPENSES = "/api/v1/expenses/"
SUMMARY = "/api/v1/expenses/summary"


def test_crear_gasto_devuelve_la_categoria_anidada(
    client: TestClient, auth_headers: dict[str, str], category_id: int
) -> None:
    response = client.post(
        EXPENSES,
        json={"amount": "12.35", "category_id": category_id, "spent_on": "2026-09-10"},
        headers=auth_headers,
    )

    assert response.status_code == 201

    body = response.json()
    assert body["amount"] == "12.35"
    assert body["category"]["name"] == "Comida"


def test_gasto_sin_fecha_usa_hoy(
    client: TestClient, auth_headers: dict[str, str], category_id: int
) -> None:
    response = client.post(
        EXPENSES,
        json={"amount": "5.00", "category_id": category_id},
        headers=auth_headers,
    )

    assert response.json()["spent_on"] == date.today().isoformat()


@pytest.mark.parametrize("amount", ["-5.00", "0", "12.999"])
def test_importes_invalidos_devuelven_422(
    client: TestClient, auth_headers: dict[str, str], category_id: int, amount: str
) -> None:
    response = client.post(
        EXPENSES,
        json={"amount": amount, "category_id": category_id},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_categoria_ajena_en_un_gasto_devuelve_422(
    client: TestClient, other_headers: dict[str, str], category_id: int
) -> None:
    response = client.post(
        EXPENSES,
        json={"amount": "10.00", "category_id": category_id},
        headers=other_headers,
    )

    assert response.status_code == 422


def test_el_listado_devuelve_el_total_sin_paginar(
    client: TestClient, auth_headers: dict[str, str], category_id: int
) -> None:
    for importe in ["10.00", "20.00", "30.00"]:
        client.post(
            EXPENSES,
            json={"amount": importe, "category_id": category_id},
            headers=auth_headers,
        )

    body = client.get(f"{EXPENSES}?limit=2", headers=auth_headers).json()

    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["limit"] == 2


def test_filtro_por_rango_de_fechas(
    client: TestClient, auth_headers: dict[str, str], category_id: int
) -> None:
    for fecha in ["2026-08-30", "2026-09-10", "2026-09-20"]:
        client.post(
            EXPENSES,
            json={"amount": "10.00", "category_id": category_id, "spent_on": fecha},
            headers=auth_headers,
        )

    body = client.get(
        f"{EXPENSES}?spent_from=2026-09-01&spent_to=2026-09-15", headers=auth_headers
    ).json()

    assert body["total"] == 1
    assert body["items"][0]["spent_on"] == "2026-09-10"


def test_rango_de_fechas_invertido_devuelve_422(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{EXPENSES}?spent_from=2026-09-20&spent_to=2026-09-01", headers=auth_headers
    )

    assert response.status_code == 422


def test_summary_agrupa_y_suma_por_categoria(
    client: TestClient, auth_headers: dict[str, str], category_id: int
) -> None:
    ocio_id = client.post(
        "/api/v1/categories/", json={"name": "Ocio"}, headers=auth_headers
    ).json()["id"]

    for importe, cid in [
        ("10.00", category_id),
        ("20.50", category_id),
        ("5.00", ocio_id),
    ]:
        client.post(
            EXPENSES,
            json={"amount": importe, "category_id": cid},
            headers=auth_headers,
        )

    body = client.get(SUMMARY, headers=auth_headers).json()

    assert Decimal(body["total"]) == Decimal("35.50")

    grupos = {g["category_name"]: g for g in body["by_category"]}
    assert Decimal(grupos["Comida"]["total"]) == Decimal("30.50")
    assert grupos["Comida"]["count"] == 2
    assert grupos["Ocio"]["count"] == 1


def test_el_summary_no_mezcla_usuarios(
    client: TestClient,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
    category_id: int,
) -> None:
    client.post(
        EXPENSES,
        json={"amount": "10.00", "category_id": category_id},
        headers=auth_headers,
    )

    body = client.get(SUMMARY, headers=other_headers).json()

    assert Decimal(body["total"]) == Decimal("0")
    assert body["by_category"] == []


def test_cada_usuario_solo_ve_sus_gastos(
    client: TestClient,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
    category_id: int,
) -> None:
    client.post(
        EXPENSES,
        json={"amount": "10.00", "category_id": category_id},
        headers=auth_headers,
    )
    otra_categoria = client.post(
        "/api/v1/categories/", json={"name": "Ocio"}, headers=other_headers
    ).json()["id"]
    client.post(
        EXPENSES,
        json={"amount": "99.00", "category_id": otra_categoria},
        headers=other_headers,
    )

    de_ana = client.get(EXPENSES, headers=auth_headers).json()
    de_pepe = client.get(EXPENSES, headers=other_headers).json()

    assert de_ana["total"] == 1
    assert de_pepe["total"] == 1
    assert de_ana["items"][0]["amount"] == "10.00"
    assert de_pepe["items"][0]["amount"] == "99.00"


def test_gasto_ajeno_devuelve_404(
    client: TestClient,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
    category_id: int,
) -> None:
    gasto_id = client.post(
        EXPENSES,
        json={"amount": "10.00", "category_id": category_id},
        headers=auth_headers,
    ).json()["id"]

    respuestas = [
        client.get(f"{EXPENSES}{gasto_id}", headers=other_headers),
        client.patch(
            f"{EXPENSES}{gasto_id}", json={"amount": "1.00"}, headers=other_headers
        ),
        client.delete(f"{EXPENSES}{gasto_id}", headers=other_headers),
    ]

    assert [r.status_code for r in respuestas] == [404, 404, 404]
