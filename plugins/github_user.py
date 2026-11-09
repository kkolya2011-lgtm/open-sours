import aiohttp
from registry import plugin
from config import cfg

async def _run(query: str, **_):
    nick = query.strip().lstrip("@")
    headers = {"User-Agent": "osintbot", "Accept": "application/vnd.github+json"}
    if cfg.github_token: headers["Authorization"] = f"Bearer {cfg.github_token}"
    async with aiohttp.ClientSession(headers=headers) as s:
        async with s.get(f"https://api.github.com/users/{nick}", timeout=cfg.timeout) as r:
            if r.status == 404: return f"GitHub {nick}: профиля нет"
            if r.status == 403: return "GitHub: лимит API"
            if r.status != 200: return f"GitHub: HTTP {r.status}"
            user = await r.json()
    out = [f"GitHub {nick}:"]
    for k in ("name", "login", "company", "blog", "location", "email", "bio", "twitter_username", "public_repos", "followers"):
        v = user.get(k)
        if v: out.append(f"  {k}: {v}")
    return "\n".join(out)

plugin("github_user", "Публичный профиль GitHub по нику", ("nick",))(_run)
