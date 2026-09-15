import asyncio
import logging
import sys
from pathlib import Path

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

from config import Settings
from drafts import build_alert_message
from filters import job_matches_filters
from notifier import notify
from parser import parse_job_message
from storage import init_db, is_seen, mark_seen

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)
RECENT_LIMIT = 20
MAX_CATCHUP_ALERTS = 5


def _require_session(path: Path) -> None:
    if not path.exists():
        raise SystemExit(
            f"Missing session file: {path}\n"
            "Run this first (once): python login.py\n"
            "Then copy referral_bot.session to the VPS with the rest of the project."
        )


async def _require_authorized(client: TelegramClient) -> None:
    if not await client.is_user_authorized():
        raise SystemExit(
            "Telegram session is not logged in.\n"
            "Run: python login.py"
        )


async def process_text(
    client: TelegramClient,
    settings: Settings,
    channel_id: str,
    text: str,
) -> bool:
    text = (text or "").strip()
    if len(text) < 20:
        return False
    if await is_seen(channel_id, text):
        return False

    job = parse_job_message(text)
    result = job_matches_filters(job, settings)
    await mark_seen(channel_id, text)

    if not result.matched:
        logger.info("Skipped: %s", job.title_hint or text[:60].replace("\n", " "))
        return False

    alert = build_alert_message(job, result.matched_via, your_name=settings.your_name)
    await notify(client, settings, alert)
    logger.info("Alert sent: %s", job.title_hint or text[:60].replace("\n", " "))
    return True


async def handle_message(
    event: events.NewMessage.Event,
    client: TelegramClient,
    settings: Settings,
) -> None:
    msg = event.message
    text = (msg.message or getattr(msg, "raw_text", None) or "").strip()
    await process_text(client, settings, str(event.chat_id), text)


async def scan_recent(client: TelegramClient, settings: Settings) -> None:
    sent = 0
    for chat in settings.monitor_channels:
        async for message in client.iter_messages(chat, limit=RECENT_LIMIT):
            if sent >= MAX_CATCHUP_ALERTS:
                return
            text = (message.message or "").strip()
            try:
                if await process_text(client, settings, str(message.chat_id), text):
                    sent += 1
            except Exception:
                logger.exception("Failed to process recent message")
    logger.info("Recent scan finished (%s alerts)", sent)


async def run_bot() -> None:
    settings = Settings.from_env()
    if not settings.monitor_channels:
        raise SystemExit("Set MONITOR_CHANNELS in .env — run: python list_chats.py")

    _require_session(settings.session_path)
    await init_db()

    client = TelegramClient(
        str(settings.session_path.with_suffix("")),
        settings.api_id,
        settings.api_hash,
    )

    @client.on(events.NewMessage(chats=settings.monitor_channels))
    async def on_new_message(event: events.NewMessage.Event) -> None:
        try:
            await handle_message(event, client, settings)
        except FloodWaitError as exc:
            logger.warning("Flood wait %ss", exc.seconds)
            await asyncio.sleep(exc.seconds + 1)
        except Exception:
            logger.exception("Failed to process message")

    await client.connect()
    await _require_authorized(client)

    me = await client.get_me()
    logger.info("Logged in as %s (%s)", me.username or me.first_name, me.id)

    names = []
    for chat in settings.monitor_channels:
        entity = await client.get_entity(chat)
        title = getattr(entity, "title", None) or getattr(entity, "username", None) or str(chat)
        names.append(f"{title} ({chat})")
        logger.info("Watching: %s", names[-1])

    try:
        await notify(
            client,
            settings,
            "Referral bot is running.\n\n"
            f"Watching:\n" + "\n".join(f"• {n}" for n in names) + "\n\n"
            "Filters: intern/trainee OR remote\n"
            "Keep this running (or put it on VPS) to get new job alerts.\n"
            "Scanning last few posts now...",
        )
        logger.info("Startup ping sent to %s", settings.alert_chat_id)
    except Exception:
        logger.exception("Could not send startup ping — check ALERT_CHAT_ID")

    try:
        await scan_recent(client, settings)
    except Exception:
        logger.exception("Recent scan failed")

    await client.run_until_disconnected()


async def main() -> None:
    while True:
        try:
            await run_bot()
        except SystemExit:
            raise
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Stopped")
            return
        except Exception:
            logger.exception("Bot crashed, restarting in 15s")
            await asyncio.sleep(15)
        else:
            logger.warning("Disconnected from Telegram, reconnecting in 15s")
            await asyncio.sleep(15)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("Stopped")
