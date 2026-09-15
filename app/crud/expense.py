from sqlalchemy import exists, select
from sqlalchemy.orm import Session, selectinload

from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


def get_expense(db: Session, expense_id: int) -> Expense | None:
    stmt = (
        select(Expense)
        .where(Expense.id == expense_id)
        .options(selectinload(Expense.category))
    )
    return db.execute(stmt).scalar_one_or_none()


def get_expenses(db: Session, skip: int = 0, limit: int = 10) -> list[Expense]:
    stmt = (
        select(Expense)
        .offset(skip)
        .limit(limit)
        .order_by(Expense.spent_on.desc(), Expense.id.desc())
        .options(selectinload(Expense.category))
    )
    return list(db.execute(stmt).scalars().all())


def create_expense(db: Session, data: ExpenseCreate) -> Expense:
    expense = Expense(**data.model_dump())

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


def category_has_expenses(db: Session, category_id: int) -> bool:
    stmt = select(exists().where(Expense.category_id == category_id))
    result = db.execute(stmt).scalar()

    return bool(result)
