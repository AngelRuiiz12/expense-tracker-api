from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status

import app.crud.category as category_crud
import app.crud.expense as expense_crud
from app.api.deps import CurrentUser, DbSession
from app.models.expense import Expense
from app.schemas.expense import (
    CategorySummary,
    ExpenseCreate,
    ExpenseList,
    ExpenseRead,
    ExpenseSummary,
    ExpenseUpdate,
)

router = APIRouter()


def _check_date_range(spent_from: date | None, spent_to: date | None) -> None:
    if spent_from is not None and spent_to is not None and spent_from > spent_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="spent_from no puede ser posterior a spent_to",
        )


@router.get("/", response_model=ExpenseList)
def list_expenses(
    db: DbSession,
    user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    category_id: int | None = Query(default=None),
    spent_from: date | None = Query(default=None),
    spent_to: date | None = Query(default=None),
) -> ExpenseList:
    _check_date_range(spent_from, spent_to)

    items = expense_crud.get_expenses(
        db, user.id, skip, limit, category_id, spent_from, spent_to
    )
    total = expense_crud.count_expenses(db, user.id, category_id, spent_from, spent_to)

    return ExpenseList(items=items, total=total, skip=skip, limit=limit)


@router.get("/summary", response_model=ExpenseSummary)
def expenses_summary(
    db: DbSession,
    user: CurrentUser,
    spent_from: date | None = Query(default=None),
    spent_to: date | None = Query(default=None),
) -> ExpenseSummary:
    _check_date_range(spent_from, spent_to)

    rows = expense_crud.summarize_by_category(db, user.id, spent_from, spent_to)
    by_category = [CategorySummary.model_validate(row) for row in rows]
    total = sum((group.total for group in by_category), Decimal("0"))

    return ExpenseSummary(total=total, by_category=by_category)


@router.post("/", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(db: DbSession, data: ExpenseCreate, user: CurrentUser) -> Expense:
    category = category_crud.get_category(db, data.category_id, user.id)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"La categoría {data.category_id} no existe",
        )

    return expense_crud.create_expense(db, data, user.id)


@router.get("/{expense_id}", response_model=ExpenseRead)
def read_expense(db: DbSession, user: CurrentUser, expense_id: int) -> Expense:
    expense = expense_crud.get_expense(db, expense_id, user.id)

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El gasto {expense_id} no existe",
        )

    return expense


@router.patch("/{expense_id}", response_model=ExpenseRead)
def patch_expense(
    db: DbSession, user: CurrentUser, expense_id: int, data: ExpenseUpdate
) -> Expense:
    expense = expense_crud.get_expense(db, expense_id, user.id)

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El gasto {expense_id} no existe",
        )

    if (
        data.category_id is not None
        and category_crud.get_category(db, data.category_id, user.id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"La categoría {data.category_id} no existe",
        )

    return expense_crud.update_expense(db, expense, data)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_expense(db: DbSession, user: CurrentUser, expense_id: int) -> None:
    expense = expense_crud.get_expense(db, expense_id, user.id)

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El gasto {expense_id} no existe",
        )

    expense_crud.delete_expense(db, expense)
