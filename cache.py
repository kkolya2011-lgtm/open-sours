import json
import time
import hashlib
import aiosqlite

DB = "cache.db"

async def init() -> None:
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS cache(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                ts INTEGER NOT NULL
            )
            """
        )
        await db.execute("CREATE INDEX IF NOT EXISTS idx_cache_ts ON cache(ts)")
        await db.commit()

def _key(plugin: str, q: str) -> str:
    return hashlib.sha256(f"{plugin}|{q.lower()}".encode()).hexdigest()

async def get(plugin: str, q: str, ttl: int) -> str | None:
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT value, ts FROM cache WHERE key = ?", (_key(plugin, q),)
        ) as cur:
            row = await cur.fetchone()
    if not row:
        return None
    value, ts = row
    if time.time() - ts > ttl:
        return None
    return json.loads(value)

async def put(plugin: str, q: str, value: str) -> None:
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO cache(key, value, ts) VALUES(?, ?, ?)",
            (_key(plugin, q), json.dumps(value, ensure_ascii=False), int(time.time())),
        )
        await db.commit()

async def cleanup(ttl: int) -> int:
    cutoff = int(time.time()) - ttl
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("DELETE FROM cache WHERE ts < ?", (cutoff,))
        await db.commit()
        return cur.rowcount or 0
