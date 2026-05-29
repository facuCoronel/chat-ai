from __future__ import annotations

import logging

import httpx

from app.domain.services.whatsapp_client import IWhatsAppClient, WhatsAppSendResult

logger = logging.getLogger(__name__)

_GRAPH_API_BASE = "https://graph.facebook.com/v20.0"


class HttpxWhatsAppClient(IWhatsAppClient):
    def __init__(self, access_token: str, timeout: float = 15.0) -> None:
        self._access_token = access_token
        self._timeout = timeout

    async def send_text(self, to: str, text: str, phone_number_id: str) -> WhatsAppSendResult:
        url = f"{_GRAPH_API_BASE}/{phone_number_id}/messages"
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
                body = exc.response.text
                logger.error("whatsapp send error status=%d body=%s", exc.response.status_code, body)
                raise RuntimeError(f"WhatsApp API {exc.response.status_code}: {body}") from exc

        wamid = response.json()["messages"][0]["id"]
        logger.info("whatsapp send ok wamid=%s to=%s", wamid, to)
        return WhatsAppSendResult(wamid=wamid)

    async def download_media(self, media_id: str) -> bytes:
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                # Step 1: resolve the CDN URL
                meta_url = f"{_GRAPH_API_BASE}/{media_id}"
                logger.info("whatsapp media resolve media_id=%s", media_id)
                resolve = await client.get(meta_url, headers=headers)
                resolve.raise_for_status()
                cdn_url = resolve.json()["url"]

                # Step 2: download the binary content
                logger.info("whatsapp media download cdn_url=%.80s", cdn_url)
                media_response = await client.get(cdn_url, headers=headers)
                media_response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                body = exc.response.text
                logger.error(
                    "whatsapp media download error status=%d body=%.200s",
                    exc.response.status_code,
                    body,
                )
                raise RuntimeError(f"WhatsApp media API {exc.response.status_code}: {body}") from exc

        logger.info("whatsapp media downloaded media_id=%s bytes=%d", media_id, len(media_response.content))
        return media_response.content
