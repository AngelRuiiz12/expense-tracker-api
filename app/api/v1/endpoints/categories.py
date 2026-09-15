from fastapi import APIRouter, HTTPException, Query, status

import app.crud.category as category_crud
import app.crud.expense as expense_crud
from app.api.deps import CurrentUser, DbSession
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter()


@router.get("/", response_model=list[CategoryRead])
def list_categories(
    db: DbSession,
    user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
) -> list[Category]:
    return category_crud.get_categories(db, user.id, skip, limit)


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(db: DbSession, user: CurrentUser, data: CategoryCreate) -> Category:
    exists_category = category_crud.get_category_by_name(db, data.name, user.id)

    if exists_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una categoría con ese nombre",
        )

    return category_crud.create_category(db, data, user.id)


@router.get("/{category_id}", response_model=CategoryRead)
def read_category(db: DbSession, user: CurrentUser, category_id: int) -> Category:
    category = category_crud.get_category(db, category_id, user.id)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La categoría {category_id} no existe",
        )

    return category


@router.patch("/{category_id}", response_model=CategoryRead)
def patch_category(
    db: DbSession, user: CurrentUser, category_id: int, data: CategoryUpdate
) -> Category:
    category = category_crud.get_category(db, category_id, user.id)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La categoría {category_id} no existe",
        )

    if (
        data.name is not None
        and data.name != category.name
        and category_crud.get_category_by_name(db, data.name, user.id)
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una categoría con ese nombre",
        )

    return category_crud.update_category(db, category, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_category(db: DbSession, user: CurrentUser, category_id: int) -> None:
    category = category_crud.get_category(db, category_id, user.id)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La categoría {category_id} no existe",
        )

    has_expenses = expense_crud.category_has_expenses(db, category_id, user.id)

    if has_expenses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La categoría {category_id} aun tiene gastos asociados",
        )

    category_crud.delete_category(db, category)
