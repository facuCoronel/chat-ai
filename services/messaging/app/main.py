from fastapi import FastAPI

from app.infrastructure.routes.conversation_router import router as conversation_router
from app.infrastructure.routes.reply_router import router as reply_router
from app.infrastructure.routes.webhook_router import router
from app.infrastructure.routes.websocket_router import router as ws_router

app = FastAPI(
    title="Messaging Service",
    description="Webhook receiver for WhatsApp (and future Instagram/Facebook) messages.",
    version="0.1.0",
)

app.include_router(router, prefix="/api/v1", tags=["webhook"])
app.include_router(reply_router, prefix="/api/v1", tags=["messages"])
app.include_router(conversation_router, prefix="/api/v1", tags=["conversations"])
app.include_router(ws_router, tags=["realtime"])


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}
