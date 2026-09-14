from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models  # noqa: F401
from app.api.v1.router import router as api_router
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Expense Tracker API", version="0.1.0", lifespan=lifespan)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
