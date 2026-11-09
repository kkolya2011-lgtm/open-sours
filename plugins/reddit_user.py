import aiohttp
from registry import plugin
from config import cfg

async def _run(query: str, **_):
    nick = query.strip().lstrip("@")
    headers = {"User-Agent": "osintbot/1.0"}
    async with aiohttp.ClientSession(headers=headers) as s:
        async with s.get(f"https://www.reddit.com/user/{nick}/about.json", timeout=cfg.timeout) as r:
            if r.status == 404: return f"Reddit {nick}: профиля нет"
            if r.status != 200: return f"Reddit: HTTP {r.status}"
            data = await r.json()
    d = (data.get("data") or {})
    if not d: return f"Reddit {nick}: пусто"
    out = [f"Reddit {nick}:"]
    for k in ("name", "created_utc", "link_karma", "comment_karma", "is_mod", "is_gold"):
        v = d.get(k)
        if v not in (None, "", 0, False): out.append(f"  {k}: {v}")
    return "\n".join(out)

plugin("reddit_user", "Публичный профиль Reddit по нику", ("nick",))(_run)
