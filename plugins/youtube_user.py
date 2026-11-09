import aiohttp
from registry import plugin
from config import cfg

async def _run(query: str, **_):
    if not cfg.youtube_key: return "YouTube: ключ не задан (YOUTUBE_API_KEY)"
    nick = query.strip().lstrip("@")
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {"part": "snippet", "q": nick, "type": "channel", "maxResults": 5, "key": cfg.youtube_key}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, params=params, timeout=cfg.timeout) as r:
            if r.status != 200: return f"YouTube: HTTP {r.status}"
            data = await r.json()
    items = data.get("items") or []
    if not items: return f"YouTube {nick}: ничего"
    out = [f"YouTube «{nick}»:"]
    for it in items:
        sn = it.get("snippet") or {}
        cid = (it.get("id") or {}).get("channelId", "")
        out.append(f"  - {sn.get('title')}\n    https://www.youtube.com/channel/{cid}")
    return "\n".join(out)

plugin("youtube_user", "Поиск канала YouTube по нику", ("nick",))(_run)
