import logging
from urllib.parse import quote

import httpx
from telethon import TelegramClient

from config import Settings

logger = logging.getLogger(__name__)
MAX_TELEGRAM_LEN = 3900


def _chunks(text: str, size: int = MAX_TELEGRAM_LEN) -> list[str]:
    if len(text) <= size:
        return [text]
    parts = []
    while text:
        parts.append(text[:size])
        text = text[size:]
    return parts


async def send_telegram_alert(client: TelegramClient, settings: Settings, message: str) -> None:
    if settings.bot_token:
        await _send_via_bot(settings, message)
        return
    for chunk in _chunks(message):
        await client.send_message(settings.alert_chat_id, chunk)


async def _send_via_bot(settings: Settings, message: str) -> None:
    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=20) as http:
        for chunk in _chunks(message):
            response = await http.post(
                url,
                json={
                    "chat_id": settings.alert_chat_id,
                    "text": chunk,
                    "disable_notification": False,
                },
            )
            if response.status_code != 200:
                logger.warning("Bot alert failed: %s", response.text[:300])


async def send_whatsapp_alert(settings: Settings, message: str) -> None:
    if not settings.whatsapp_phone or not settings.callmebot_api_key:
        return

    url = (
        "https://api.callmebot.com/whatsapp.php"
        f"?phone={quote(settings.whatsapp_phone)}"
        f"&text={quote(message[:1500])}"
        f"&apikey={quote(settings.callmebot_api_key)}"
    )

    try:
        async with httpx.AsyncClient(timeout=15) as http:
            response = await http.get(url)
            if response.status_code != 200:
                logger.warning("WhatsApp alert failed: %s", response.text[:200])
    except Exception:
        logger.exception("WhatsApp alert error")


async def send_sms_alert(settings: Settings, message: str) -> None:
    if not settings.sms_to or not settings.fast2sms_api_key:
        return
    if message.startswith("Referral bot is running"):
        return

    number = settings.sms_to.replace("+", "").replace(" ", "")
    short = " ".join(message.splitlines()[:6])[:150]
    url = (
        "https://www.fast2sms.com/dev/bulkV2"
        f"?authorization={quote(settings.fast2sms_api_key)}"
        "&route=q"
        f"&message={quote(short)}"
        "&language=english"
        "&flash=0"
        f"&numbers={quote(number)}"
    )

    try:
        async with httpx.AsyncClient(timeout=15) as http:
            response = await http.get(url)
            if response.status_code != 200:
                logger.warning("SMS alert failed: %s", response.text[:200])
    except Exception:
        logger.exception("SMS alert error")


async def notify(client: TelegramClient, settings: Settings, message: str) -> None:
    await send_telegram_alert(client, settings, message)
    await send_whatsapp_alert(settings, message)
    await send_sms_alert(settings, message)
