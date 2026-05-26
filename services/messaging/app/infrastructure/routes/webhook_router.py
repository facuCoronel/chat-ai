from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.adapters.controllers.webhook_controller import WebhookController
from app.application.use_cases.receive_message import ReceiveMessageUseCase
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.dependencies import get_receive_message_use_case
from app.infrastructure.security.signature_validator import validate_meta_signature

router = APIRouter()


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
    settings: Settings = Depends(get_settings),
):
    """
    Webhook verification endpoint required by Meta when setting up the webhook URL.
    Responds with the challenge string to confirm endpoint ownership.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WEBHOOK_VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/webhook", status_code=200)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    use_case: ReceiveMessageUseCase = Depends(get_receive_message_use_case),
    settings: Settings = Depends(get_settings),
):
    """
    Webhook receiver. Returns 200 immediately and processes the payload asynchronously
    to avoid Meta retrying the delivery due to slow responses.
    """
    body = await request.body()

    signature = request.headers.get("X-Hub-Signature-256", "")
    if not validate_meta_signature(body, signature, settings.APP_SECRET):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = await request.json()
    controller = WebhookController(use_case)
    background_tasks.add_task(controller.handle_incoming, payload)

    return {"status": "ok"}
