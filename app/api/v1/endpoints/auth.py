from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import app.crud.refresh_token as refresh_crud
import app.crud.user as user_crud
from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.token import RefreshRequest, Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter()

INVALID_REFRESH = "Refresh token invalido o caducado"


def _issue_tokens(db: DbSession, user_id: int) -> Token:
    return Token(
        access_token=create_access_token(str(user_id)),
        refresh_token=refresh_crud.issue_refresh_token(db, user_id),
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(db: DbSession, data: UserCreate) -> User:
    if user_crud.get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email",
        )

    return user_crud.create_user(db, data)


@router.post("/login", response_model=Token)
def login(
    db: DbSession, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = user_crud.get_user_by_email(db, form_data.username)

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _issue_tokens(db, user.id)


@router.post("/refresh", response_model=Token)
def refresh(db: DbSession, data: RefreshRequest) -> Token:
    stored = refresh_crud.get_refresh_token(db, data.refresh_token)

    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido o caducado",
        )

    if stored.revoked_at is not None:
        refresh_crud.revoke_all_for_user(db, stored.user_id)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido o caducado",
        )

    if stored.expires_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido o caducado",
        )

    refresh_crud.revoke(db, stored)

    return _issue_tokens(db, stored.user_id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(db: DbSession, data: RefreshRequest) -> None:
    stored = refresh_crud.get_refresh_token(db, data.refresh_token)

    if stored is not None and stored.revoked_at is None:
        refresh_crud.revoke(db, stored)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(db: DbSession, user: CurrentUser) -> None:
    refresh_crud.revoke_all_for_user(db, user.id)
