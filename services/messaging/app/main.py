from fastapi import FastAPI

from app.infrastructure.routes.webhook_router import router

app = FastAPI(
    title="Messaging Service",
    description="Webhook receiver for WhatsApp (and future Instagram/Facebook) messages.",
    version="0.1.0",
)

app.include_router(router, prefix="/api/v1", tags=["webhook"])


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}
