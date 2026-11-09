import asyncio
import aiohttp
from registry import plugin
from config import cfg

SITES: list[tuple[str, str, int]] = [
    ("VK", "site:vk.com", 5),
    ("OK", "site:ok.ru", 5),
    ("Telegram", "site:t.me", 5),
    ("Instagram", "site:instagram.com", 5),
    ("TikTok", "site:tiktok.com", 5),
    ("Habr", "site:habr.com", 5),
    ("HH.ru", "site:hh.ru", 5),
    ("Avito", "site:avito.ru", 5),
    ("GitHub", "site:github.com", 5),
    ("Drive2", "site:drive2.ru", 3),
    ("Pikabu", "site:pikabu.ru", 3),
    ("Dzen", "site:dzen.ru", 3),
]

_semaphore = asyncio.Semaphore(4)

async def _serper(query: str, site_filter: str, num: int) -> list[dict]:
    if not cfg.serper_key: return []
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": cfg.serper_key, "Content-Type": "application/json"}
    payload = {"q": f"{query} {site_filter}", "num": num}
    async with _semaphore:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(url, headers=headers, json=payload, timeout=cfg.timeout) as r:
                    if r.status != 200: return []
                    data = await r.json()
            return data.get("organic", []) or []
        except Exception:
            return []

async def _run(query: str, **_):
    q = query.strip()
    if not cfg.serper_key:
        return "people_search: нужен SERPER_API_KEY."
    tasks = [_serper(q, site_filter, num) for _, site_filter, num in SITES]
    results = await asyncio.gather(*tasks)
    out = [f"Публичный поиск «{q}»:"]
    found = 0
    for (name, _, _), items in zip(SITES, results):
        if not items: continue
        out.append(f"  {name}:")
        for it in items:
            out.append(f"    - {it.get('title', '')}\n      {it.get('link', '')}")
            found += 1
    if found == 0: out.append("  (ничего не найдено)")
    return "\n".join(out)

plugin("people_search", "Поиск по ФИО/нику через Google", ("name", "nick"))(_run)
