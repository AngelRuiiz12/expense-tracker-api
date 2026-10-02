from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.crud.refresh_token as refresh_crud
from app.models.refresh_token import RefreshToken
from app.models.user import User

AYER = timedelta(days=-1)
MANANA = timedelta(days=1)


def _crear_usuario(db: Session) -> User:
    user = User(email="ana@test.com", hashed_password="no-importa")
    db.add(user)
    db.commit()

    return user


def _token(
    user: User, token_hash: str, *, caduca_en: timedelta, revocado: bool
) -> RefreshToken:
    ahora = datetime.now(UTC)

    return RefreshToken(
        token_hash=token_hash,
        user_id=user.id,
        expires_at=ahora + caduca_en,
        revoked_at=ahora if revocado else None,
    )


def _hashes_guardados(db: Session) -> set[str]:
    return set(db.execute(select(RefreshToken.token_hash)).scalars())


def test_delete_expired_borra_solo_los_caducados(db: Session) -> None:
    user = _crear_usuario(db)
    db.add_all(
        [
            _token(user, "A", caduca_en=AYER, revocado=False),
            _token(user, "B", caduca_en=AYER, revocado=True),
            _token(user, "C", caduca_en=MANANA, revocado=False),
            _token(user, "D", caduca_en=MANANA, revocado=True),
        ]
    )
    db.commit()

    borrados = refresh_crud.delete_expired(db)

    assert borrados == 2
    assert _hashes_guardados(db) == {"C", "D"}


def test_delete_expired_sin_caducados_no_toca_nada(db: Session) -> None:
    user = _crear_usuario(db)
    db.add(_token(user, "C", caduca_en=MANANA, revocado=False))
    db.commit()

    borrados = refresh_crud.delete_expired(db)

    assert borrados == 0
    assert _hashes_guardados(db) == {"C"}
