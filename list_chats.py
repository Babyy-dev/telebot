"""List groups/channels so you can copy the ID into MONITOR_CHANNELS."""

import asyncio

from telethon import TelegramClient

from config import Settings


async def main() -> None:
    settings = Settings.from_env()
    session = str(settings.session_path.with_suffix(""))
    client = TelegramClient(session, settings.api_id, settings.api_hash)
    await client.start()

    if not await client.is_user_authorized():
        raise SystemExit("Not logged in. Run: python login.py")

    print("\nYour groups & channels — copy the ID into .env MONITOR_CHANNELS:\n")
    print(f"{'ID':<18}  {'Name'}")
    print("-" * 60)

    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            print(f"{dialog.id:<18}  {dialog.name}")

    print("\nPrivate groups use the numeric ID, for example:")
    print("MONITOR_CHANNELS=-1001234567890")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
