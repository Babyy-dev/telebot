import hashlib
from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent / "referrals.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_messages (
                message_hash TEXT PRIMARY KEY,
                channel_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()


def _hash_message(channel_id: str, text: str) -> str:
    payload = f"{channel_id}:{text.strip()}"
    return hashlib.sha256(payload.encode()).hexdigest()


async def is_seen(channel_id: str, text: str) -> bool:
    message_hash = _hash_message(channel_id, text)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM seen_messages WHERE message_hash = ?",
            (message_hash,),
        )
        row = await cursor.fetchone()
        return row is not None


async def mark_seen(channel_id: str, text: str) -> None:
    message_hash = _hash_message(channel_id, text)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO seen_messages (message_hash, channel_id) VALUES (?, ?)",
            (message_hash, channel_id),
        )
        await db.commit()
