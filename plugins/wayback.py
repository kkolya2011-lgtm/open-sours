import aiohttp
from registry import plugin
from config import cfg

async def _run(query: str, **_):
    q = query.strip()
    out = [f"Wayback «{q}»:"]
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("http://archive.org/wayback/available", params={"url": q}, timeout=cfg.timeout) as r:
                data = await r.json() if r.status == 200 else {}
    except Exception:
        data = {}

    snap = (data.get("archived_snapshots") or {}).get("closest")
    if snap:
        out.append(f"  последний снимок: {snap.get('timestamp')}")
        out.append(f"  url: {snap.get('url')}")
        out.append(f"  статус: {snap.get('status')}")
    else:
        out.append("  снимков нет")

    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("http://web.archive.org/cdx/search/cdx",
                             params={"url": q, "output": "json", "limit": "10", "fl": "timestamp,original,statuscode"},
                             timeout=cfg.timeout) as r:
                if r.status == 200:
                    rows = await r.json(content_type=None)
                    if len(rows) > 1:
                        out.append("  история (последние 10):")
                        for row in rows[1:]:
                            out.append("    " + " | ".join(str(x) for x in row))
    except Exception:
        pass
    return "\n".join(out)

plugin("wayback", "Снимки страницы в Wayback Machine", ("domain", "username", "nick"))(_run)
