from __future__ import annotations

import logging

import httpx

from app.domain.services.whatsapp_client import IWhatsAppClient, WhatsAppSendResult

logger = logging.getLogger(__name__)

_GRAPH_API_BASE = "https://graph.facebook.com/v20.0"


class HttpxWhatsAppClient(IWhatsAppClient):
    def __init__(self, phone_number_id: str, access_token: str, timeout: float = 15.0) -> None:
        self._phone_number_id = phone_number_id
        self._access_token = access_token
        self._timeout = timeout

    async def send_text(self, to: str, text: str) -> WhatsAppSendResult:
        url = f"{_GRAPH_API_BASE}/{self._phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        headers = {"Authorization": f"Bearer {self._access_token}"}

        logger.info("whatsapp send to=%s length=%d", to, len(text))
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "whatsapp send error status=%d body=%.300s",
                    exc.response.status_code,
                    exc.response.text,
                )
                raise

        wamid = response.json()["messages"][0]["id"]
        logger.info("whatsapp send ok wamid=%s to=%s", wamid, to)
        return WhatsAppSendResult(wamid=wamid)
