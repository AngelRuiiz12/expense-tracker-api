from fastapi import APIRouter

from app.api.v1.endpoints import auth, categories, expenses

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(categories.router, prefix="/categories", tags=["categories"])
router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
