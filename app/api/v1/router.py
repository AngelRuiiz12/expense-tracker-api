from fastapi import APIRouter

from app.api.v1.endpoints import categories

router = APIRouter()

router.include_router(categories.router, prefix="/categories", tags=["categories"])
