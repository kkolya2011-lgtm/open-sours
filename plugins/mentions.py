import aiohttp
from registry import plugin
from config import cfg

async def _run(query: str, **_):
    if not cfg.serper_key: return "mentions: SERPER_API_KEY не задан"
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": cfg.serper_key, "Content-Type": "application/json"}
    payload = {"q": f'"{query}"', "num": 10}
    async with aiohttp.ClientSession() as s:
        async with s.post(url, headers=headers, json=payload, timeout=cfg.timeout) as r:
            if r.status != 200: return f"mentions: HTTP {r.status}"
            data = await r.json()
    items = data.get("organic", [])
    if not items: return f"mentions «{query}»: ничего"
    out = [f"mentions «{query}» (топ {len(items)}):"]
    for it in items:
        out.append(f"  - {it.get('title', '')}\n    {it.get('link', '')}")
    return "\n".join(out)

plugin("mentions", "Упоминания в открытом вебе (Serper/Google)", ("username", "nick", "email", "domain"))(_run)
