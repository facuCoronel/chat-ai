from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.database.engine import create_tables
from app.infrastructure.routes.webhook_router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="Messaging Service",
    description="Webhook receiver for WhatsApp (and future Instagram/Facebook) messages.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1", tags=["webhook"])
