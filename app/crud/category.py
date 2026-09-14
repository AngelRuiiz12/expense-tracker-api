from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def get_category_by_name(db: Session, category_name: str) -> Category | None:
    stmt = select(Category).where(Category.name == category_name)
    category = db.execute(stmt).scalar_one_or_none()

    return category


def get_category(db: Session, category_id: int) -> Category | None:
    stmt = select(Category).where(Category.id == category_id)
    category = db.execute(stmt).scalar_one_or_none()

    return category


def get_categories(db: Session, skip: int = 0, limit: int = 10) -> list[Category]:
    stmt = select(Category).offset(skip).limit(limit)
    categories = db.execute(stmt).scalars().all()

    return list(categories)


def create_category(db: Session, data: CategoryCreate) -> Category:
    new_category = Category(**data.model_dump())

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category


def update_category(db: Session, category: Category, data: CategoryUpdate) -> Category:
    # Transformo la data en un dict que elimina los atributos que no han sido aportados.
    updates = data.model_dump(exclude_unset=True)

    for key, value in updates.items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)

    return category


def delete_category(db: Session, category: Category) -> None:
    db.delete(category)
    db.commit()
