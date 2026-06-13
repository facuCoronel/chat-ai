import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.routes.webhook_router import router
from app.infrastructure.config import get_settings

_settings = get_settings()

logging.basicConfig(
    level=getattr(logging, _settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="Messaging Service",
    description="Webhook receiver for WhatsApp messages.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["webhook"])


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}
