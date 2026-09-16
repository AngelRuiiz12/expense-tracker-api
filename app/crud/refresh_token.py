from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.security import (
    create_refresh_token,
    hash_refresh_token,
    refresh_token_expiry,
)
from app.models.refresh_token import RefreshToken


def issue_refresh_token(db: Session, user_id: int) -> str:
    token = create_refresh_token()

    db.add(
        RefreshToken(
            token_hash=hash_refresh_token(token),
            user_id=user_id,
            expires_at=refresh_token_expiry(),
        )
    )
    db.commit()

    return token


def get_refresh_token(db: Session, token: str) -> RefreshToken | None:
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == hash_refresh_token(token)
    )

    return db.execute(stmt).scalar_one_or_none()


def revoke(db: Session, refresh_token: RefreshToken) -> None:
    refresh_token.revoked_at = datetime.now(UTC)
    db.commit()


def revoke_all_for_user(db: Session, user_id: int) -> None:
    stmt = (
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    db.execute(stmt)
    db.commit()
