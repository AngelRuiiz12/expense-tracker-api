from fastapi import APIRouter, HTTPException, Query, status

import app.crud.category as category_crud
import app.crud.expense as expense_crud
from app.api.deps import DbSession
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate

router = APIRouter()


@router.get("/", response_model=list[ExpenseRead])
def list_expenses(
    db: DbSession,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
) -> list[Expense]:
    return expense_crud.get_expenses(db, skip, limit)


@router.post("/", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(db: DbSession, data: ExpenseCreate) -> Expense:
    category = category_crud.get_category(db, data.category_id)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"La categoría {data.category_id} no existe",
        )

    return expense_crud.create_expense(db, data)


@router.get("/{expense_id}", response_model=ExpenseRead)
def read_expense(db: DbSession, expense_id: int) -> Expense:
    expense = expense_crud.get_expense(db, expense_id)

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El gasto {expense_id} no existe",
        )

    return expense


@router.patch("/{expense_id}", response_model=ExpenseRead)
def patch_expense(db: DbSession, expense_id: int, data: ExpenseUpdate) -> Expense:
    expense = expense_crud.get_expense(db, expense_id)

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El gasto {expense_id} no existe",
        )

    if data.category_id is not None:
        category = category_crud.get_category(db, data.category_id)

        if category is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"La categoría {data.category_id} no existe",
            )

    return expense_crud.update_expense(db, expense, data)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_expense(db: DbSession, expense_id: int) -> None:
    expense = expense_crud.get_expense(db, expense_id)

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El gasto {expense_id} no existe",
        )

    expense_crud.delete_expense(db, expense)
