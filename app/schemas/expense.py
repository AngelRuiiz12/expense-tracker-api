from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.category import CategoryRead


class ExpenseBase(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    description: str | None = Field(default=None, max_length=100)
    spent_on: date = Field(default_factory=date.today)
    category_id: int


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    amount: Decimal | None = Field(gt=0, max_digits=10, decimal_places=2, default=None)
    description: str | None = Field(default=None, max_length=100)
    spent_on: date | None = Field(default=None)
    category_id: int | None = Field(default=None)


class ExpenseRead(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    category: CategoryRead


class ExpenseList(BaseModel):
    items: list[ExpenseRead]
    total: int
    skip: int
    limit: int


class CategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: int
    category_name: str
    total: Decimal
    count: int


class ExpenseSummary(BaseModel):
    total: Decimal
    by_category: list[CategorySummary]
