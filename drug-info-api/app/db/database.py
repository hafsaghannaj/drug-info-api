"""SQLite-backed response cache.

Schema:
    cache(key TEXT PK, value TEXT, expires_at REAL)

All values are JSON-serialised strings. Expired rows are pruned lazily
on read and eagerly via a periodic vacuum (called from lifespan).
"""
import json
import time
import aiosqlite
from app.config import get_settings

_DB: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _DB
    if _DB is None:
        settings = get_settings()
        _DB = await aiosqlite.connect(settings.cache_db_path)
        _DB.row_factory = aiosqlite.Row
    return _DB


async def init_db() -> None:
    db = await get_db()
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS cache (
            key        TEXT PRIMARY KEY,
            value      TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
        """
    )
    await db.commit()
    # Prune expired rows from previous runs
    await db.execute("DELETE FROM cache WHERE expires_at < ?", (time.time(),))
    await db.commit()


async def cache_get(key: str) -> dict | list | None:
    db = await get_db()
    async with db.execute(
        "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        return None
    if row["expires_at"] < time.time():
        await db.execute("DELETE FROM cache WHERE key = ?", (key,))
        await db.commit()
        return None
    return json.loads(row["value"])


async def cache_set(key: str, value: dict | list, ttl_seconds: int) -> None:
    db = await get_db()
    await db.execute(
        "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
        (key, json.dumps(value), time.time() + ttl_seconds),
    )
    await db.commit()
