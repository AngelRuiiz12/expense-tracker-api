from collections.abc import Sequence
from datetime import date

from sqlalchemy import ColumnElement, Row, exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


def _expense_filters(
    user_id: int,
    category_id: int | None = None,
    spent_from: date | None = None,
    spent_to: date | None = None,
) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = [Expense.user_id == user_id]

    if category_id is not None:
        conditions.append(Expense.category_id == category_id)

    if spent_from is not None:
        conditions.append(Expense.spent_on >= spent_from)

    if spent_to is not None:
        conditions.append(Expense.spent_on <= spent_to)

    return conditions


def get_expense(db: Session, expense_id: int, user_id: int) -> Expense | None:
    stmt = (
        select(Expense)
        .where(Expense.id == expense_id, Expense.user_id == user_id)
        .options(selectinload(Expense.category))
    )

    return db.execute(stmt).scalar_one_or_none()


def get_expenses(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    category_id: int | None = None,
    spent_from: date | None = None,
    spent_to: date | None = None,
) -> list[Expense]:
    stmt = (
        select(Expense)
        .where(*_expense_filters(user_id, category_id, spent_from, spent_to))
        .order_by(Expense.spent_on.desc(), Expense.id.desc())
        .offset(skip)
        .limit(limit)
        .options(selectinload(Expense.category))
    )

    return list(db.execute(stmt).scalars().all())


def count_expenses(
    db: Session,
    user_id: int,
    category_id: int | None = None,
    spent_from: date | None = None,
    spent_to: date | None = None,
) -> int:
    stmt = (
        select(func.count())
        .select_from(Expense)
        .where(*_expense_filters(user_id, category_id, spent_from, spent_to))
    )

    return db.execute(stmt).scalar_one()


def summarize_by_category(
    db: Session,
    user_id: int,
    spent_from: date | None = None,
    spent_to: date | None = None,
) -> Sequence[Row[tuple[int, str, float, int]]]:
    stmt = (
        select(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            func.sum(Expense.amount).label("total"),
            func.count(Expense.id).label("count"),
        )
        .select_from(Expense)
        .join(Expense.category)
        .where(*_expense_filters(user_id, spent_from=spent_from, spent_to=spent_to))
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Expense.amount).desc())
    )

    return db.execute(stmt).all()


def create_expense(db: Session, data: ExpenseCreate, user_id: int) -> Expense:
    expense = Expense(**data.model_dump(), user_id=user_id)

    db.add(expense)
    db.commit()
    db.refresh(expense)

    return expense


def update_expense(db: Session, expense: Expense, data: ExpenseUpdate) -> Expense:
    # Transformo la data en un dict que elimina los atributos que no han sido aportados.
    updates = data.model_dump(exclude_unset=True)

    for attr, value in updates.items():
        setattr(expense, attr, value)

    db.commit()
    db.refresh(expense)

    return expense


def delete_expense(db: Session, expense: Expense) -> None:
    db.delete(expense)
    db.commit()


def category_has_expenses(db: Session, category_id: int, user_id: int) -> bool:
    stmt = select(
        exists().where(Expense.category_id == category_id, Expense.user_id == user_id)
    )

    return bool(db.execute(stmt).scalar())
