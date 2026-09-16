# Expense Tracker API

[![CI](https://github.com/AngelRuiiz12/expense-tracker-api/actions/workflows/ci.yml/badge.svg)](https://github.com/AngelRuiiz12/expense-tracker-api/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791)](https://www.postgresql.org/)

API REST para el control de gastos personales. Cada usuario gestiona sus propias
categorías y gastos, con autenticación por JWT y refresh tokens rotativos.

Proyecto construido desde cero como ejercicio completo de backend: modelado de
datos, autenticación, aislamiento entre usuarios, migraciones, tests y despliegue
en contenedores.

---

## Características

- **Autenticación JWT** con access tokens de vida corta y refresh tokens rotativos.
- **Detección de reutilización de tokens**: si un refresh token ya usado vuelve a
  aparecer, se revocan todas las sesiones de ese usuario.
- **Aislamiento por usuario**: el filtro vive dentro de la capa de acceso a datos,
  no en los endpoints, de modo que ninguna consulta puede devolver datos ajenos.
- **Contraseñas con Argon2id** y refresh tokens almacenados como hash SHA-256.
- **Importes con `Decimal`** y columnas `NUMERIC(10,2)`: sin errores de redondeo.
- **Filtros, paginación con total** y endpoint de resumen agregado por categoría.
- **Migraciones versionadas** con Alembic.
- **39 tests de integración** contra PostgreSQL real.
- **CI en GitHub Actions**: linter, tests y build de la imagen Docker.

## Stack

| Área | Tecnología |
|---|---|
| Lenguaje | Python 3.13 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (estilo `Mapped` / `select()`) |
| Validación | Pydantic v2 + pydantic-settings |
| Base de datos | PostgreSQL 17 |
| Driver | psycopg 3 |
| Migraciones | Alembic |
| Auth | PyJWT + pwdlib (Argon2id) |
| Tests | pytest |
| Calidad | Ruff (linter + formateador) |
| Entorno | uv |
| Contenedores | Docker + Docker Compose |
| CI | GitHub Actions |

---

## Arranque rápido

Requisitos: [Docker](https://www.docker.com/) y [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/AngelRuiiz12/expense-tracker-api.git
cd expense-tracker-api
```

Copia el fichero de variables de entorno y rellénalo:

```bash
cp .env.example .env
```

Genera una clave secreta real para `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Opción A — todo en contenedores

```bash
docker compose up -d --build
```

Levanta PostgreSQL, aplica las migraciones y arranca la API en
<http://localhost:8000>.

### Opción B — solo la base de datos en Docker

Recomendado para desarrollar, porque recarga al guardar.

```bash
docker compose up -d db
```

```bash
uv sync
```

```bash
uv run alembic upgrade head
```

```bash
uv run fastapi dev app/main.py
```

### Documentación interactiva

Con la API en marcha: <http://localhost:8000/docs>

Para probar los endpoints protegidos, regístrate en `POST /auth/register`, pulsa
**Authorize** e introduce el email en el campo *username* junto a la contraseña.

---

## Endpoints

Todas las rutas cuelgan de `/api/v1`.

### Autenticación

| Método | Ruta | Auth | Descripción |
|---|---|:---:|---|
| `POST` | `/auth/register` | — | Crea una cuenta |
| `POST` | `/auth/login` | — | Devuelve access token + refresh token |
| `POST` | `/auth/refresh` | — | Renueva el par y revoca el refresh anterior |
| `POST` | `/auth/logout` | — | Revoca el refresh token indicado |
| `POST` | `/auth/logout-all` | 🔒 | Revoca todas las sesiones del usuario |

### Categorías

| Método | Ruta | Auth | Descripción |
|---|---|:---:|---|
| `GET` | `/categories/` | 🔒 | Lista las categorías del usuario |
| `POST` | `/categories/` | 🔒 | Crea una categoría |
| `GET` | `/categories/{id}` | 🔒 | Detalle |
| `PATCH` | `/categories/{id}` | 🔒 | Actualización parcial |
| `DELETE` | `/categories/{id}` | 🔒 | Borra, salvo que tenga gastos asociados |

### Gastos

| Método | Ruta | Auth | Descripción |
|---|---|:---:|---|
| `GET` | `/expenses/` | 🔒 | Lista paginada, con filtros |
| `POST` | `/expenses/` | 🔒 | Crea un gasto |
| `GET` | `/expenses/summary` | 🔒 | Total y desglose por categoría |
| `GET` | `/expenses/{id}` | 🔒 | Detalle |
| `PATCH` | `/expenses/{id}` | 🔒 | Actualización parcial |
| `DELETE` | `/expenses/{id}` | 🔒 | Elimina el gasto |

Parámetros de consulta en `GET /expenses/`: `skip`, `limit`, `category_id`,
`spent_from`, `spent_to`.

También hay un `GET /health` sin versionar, para comprobaciones de estado.

### Ejemplo

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=ana@ejemplo.com&password=secreta123"
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "8PIdgKTM28E5Cpm4h5...",
  "token_type": "Bearer"
}
```

```bash
curl http://localhost:8000/api/v1/expenses/summary \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

```json
{
  "total": "75.20",
  "by_category": [
    { "category_id": 1, "category_name": "Gasolina", "total": "75.20", "count": 2 }
  ]
}
```

---

## Modelo de datos

```
User ──< Category ──< Expense
  │                     │
  └─────────────────────┘
  │
  └──< RefreshToken
```

- Un usuario tiene muchas categorías, muchos gastos y muchos refresh tokens.
- Cada gasto pertenece a una categoría **y** guarda su propio `user_id`, lo que
  permite filtrar por usuario sin un `JOIN` en cada consulta.
- La unicidad del nombre de categoría es compuesta, `(user_id, name)`: dos
  usuarios distintos pueden tener cada uno su categoría "Comida".

## Estructura del proyecto

```
app/
├── main.py                 # instancia de FastAPI y montaje de routers
├── core/
│   ├── config.py           # configuración leída del entorno
│   └── security.py         # hashing, JWT y generación de tokens
├── db/
│   ├── base.py             # Base declarativa y convención de nombres
│   └── session.py          # engine y fábrica de sesiones
├── models/                 # SQLAlchemy: cómo se guardan los datos
├── schemas/                # Pydantic: qué entra y sale por HTTP
├── crud/                   # acceso a datos, sin lógica HTTP
└── api/
    ├── deps.py             # dependencias: sesión y usuario actual
    └── v1/
        ├── router.py
        └── endpoints/      # routing, validación y códigos de estado
alembic/versions/           # migraciones versionadas
tests/                      # suite de integración
```

Cada capa tiene una responsabilidad única: los endpoints no escriben consultas y
el CRUD no sabe que existe HTTP. Los schemas de Pydantic son el contrato de la
API y son deliberadamente distintos de los modelos de base de datos.

---

## Desarrollo

```bash
uv run pytest                   # tests (requiere el contenedor de BD)
uv run ruff check .             # linter
uv run ruff format .            # formateador
uv run alembic upgrade head     # aplicar migraciones
uv run alembic downgrade -1     # deshacer la última
```

Tras modificar un modelo:

```bash
uv run alembic revision --autogenerate -m "descripción del cambio"
```

Revisa siempre el fichero generado antes de aplicarlo: Alembic no detecta los
renombrados de columna y los interpreta como borrar y crear.

### Tests

Los 39 tests se ejecutan contra una base de datos PostgreSQL real
(`expense_tracker_test`), no contra SQLite en memoria, para que ejerciten el
mismo motor que usa la aplicación: claves ajenas, tipos estrictos y `GROUP BY`
estricto.

---

## Decisiones de diseño

**El filtro por usuario vive en el CRUD, no en los endpoints.** Las funciones de
acceso a datos exigen `user_id` en su firma, así que es imposible olvidarlo: si
falta, el código no llega a ejecutarse. Un recurso ajeno devuelve `404` y no
`403`, para no revelar que existe.

**El refresh token no es un JWT.** Como hay que consultar la base de datos de
todos modos para poder revocarlo, un JWT no aportaría nada y sí añadiría
superficie de ataque. Es una cadena aleatoria opaca de 256 bits.

**Argon2id para contraseñas, SHA-256 para refresh tokens.** Argon2 es lento a
propósito para frenar ataques de diccionario sobre secretos elegidos por
personas. Un token aleatorio no es adivinable, y además su búsqueda en la tabla
exige un hash determinista, algo que la sal aleatoria de Argon2 impide.

**El esquema lo gestiona Alembic en exclusiva.** La aplicación no ejecuta
`create_all`, de modo que no necesita permisos para crear tablas en producción.

---

## Estado y limitaciones conocidas

- Los refresh tokens caducados y revocados **no se purgan**: falta una tarea
  periódica de limpieza.
- No hay límite de intentos en `/auth/login`, lo que deja la puerta abierta a
  ataques de fuerza bruta.
- Las columnas `created_at` de las tablas anteriores a `refresh_tokens` son
  `TIMESTAMP` sin zona horaria; deberían migrarse a `TIMESTAMPTZ`.
- No hay configuración de CORS, necesaria antes de conectar un frontend.

---

## Licencia

[MIT](LICENSE)
