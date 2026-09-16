import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _csv(value: str | None) -> list[str]:
    if not value or not value.strip():
        return []
    return [part.strip().lower() for part in value.split(",") if part.strip()]


def _channels(value: str | None) -> list[int | str]:
    if not value or not value.strip():
        return []
    result: list[int | str] = []
    for part in value.split(","):
        part = part.strip().lstrip("@")
        if not part:
            continue
        if part.lstrip("-").isdigit():
            result.append(int(part))
        else:
            result.append(part)
    return result


@dataclass
class Settings:
    api_id: int
    api_hash: str
    monitor_channels: list[int | str]
    alert_chat_id: int
    bot_token: str | None = None
    whatsapp_phone: str | None
    callmebot_api_key: str | None
    sms_to: str | None = None
    fast2sms_api_key: str | None = None
    filter_roles: list[str] = field(default_factory=list)
    filter_work_modes: list[str] = field(default_factory=list)
    filter_locations: list[str] = field(default_factory=list)
    your_name: str = "Your Name"
    session_path: Path = BASE_DIR / "referral_bot.session"

    @classmethod
    def from_env(cls) -> "Settings":
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        alert_chat_id = os.getenv("ALERT_CHAT_ID")
        monitor_channels = _channels(os.getenv("MONITOR_CHANNELS"))

        if not api_id or not api_hash:
            raise ValueError("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env")
        if not alert_chat_id:
            raise ValueError("Set ALERT_CHAT_ID in .env (message @userinfobot)")

        return cls(
            api_id=int(api_id),
            api_hash=api_hash,
            monitor_channels=monitor_channels,
            alert_chat_id=int(alert_chat_id),
            bot_token=(os.getenv("TELEGRAM_BOT_TOKEN") or "").strip() or None,
            whatsapp_phone=os.getenv("WHATSAPP_PHONE"),
            callmebot_api_key=os.getenv("CALLMEBOT_API_KEY"),
            sms_to=os.getenv("SMS_TO"),
            fast2sms_api_key=os.getenv("FAST2SMS_API_KEY"),
            filter_roles=_csv(os.getenv("FILTER_ROLES")),
            filter_work_modes=_csv(os.getenv("FILTER_WORK_MODES")),
            filter_locations=_csv(os.getenv("FILTER_LOCATIONS")),
            your_name=os.getenv("YOUR_NAME", "Your Name").strip() or "Your Name",
        )
