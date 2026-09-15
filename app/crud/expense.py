from sqlalchemy import exists, select
from sqlalchemy.orm import Session, selectinload

from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


def get_expense(db: Session, expense_id: int, user_id: int) -> Expense | None:
    stmt = (
        select(Expense)
        .where(Expense.id == expense_id, Expense.user_id == user_id)
        .options(selectinload(Expense.category))
    )

    return db.execute(stmt).scalar_one_or_none()


def get_expenses(
    db: Session, user_id: int, skip: int = 0, limit: int = 10
) -> list[Expense]:
    stmt = (
        select(Expense)
        .where(Expense.user_id == user_id)
        .order_by(Expense.spent_on.desc(), Expense.id.desc())
        .offset(skip)
        .limit(limit)
        .options(selectinload(Expense.category))
    )

    return list(db.execute(stmt).scalars().all())


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
