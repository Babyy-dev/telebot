"""One-time Telegram login. Run before starting the bot."""

import asyncio

from telethon import TelegramClient

from config import Settings


async def main() -> None:
    settings = Settings.from_env()
    session = str(settings.session_path.with_suffix(""))
    client = TelegramClient(session, settings.api_id, settings.api_hash)
    await client.start()
    me = await client.get_me()
    print(f"Login OK — {me.username or me.first_name} (id {me.id})")
    print(f"Use this as ALERT_CHAT_ID: {me.id}")
    print(f"Session saved: {settings.session_path}")
    print("Next: python list_chats.py")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
