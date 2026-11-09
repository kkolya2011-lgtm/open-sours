import aiohttp
from registry import plugin
from config import cfg

CHECKS = [
    ("GitHub", "https://github.com/{u}", False),
    ("Reddit", "https://www.reddit.com/user/{u}/about.json", False),
    ("VK", "https://vk.com/{u}", False),
    ("Instagram", "https://www.instagram.com/{u}/", True),
    ("TikTok", "https://www.tiktok.com/@{u}", True),
]

NOT_FOUND_MARKERS = (
    "page isn't available",
    "page not found",
    "sorry, this page",
    "couldn't find this account",
)

async def _check(s: aiohttp.ClientSession, url: str, login_check: bool) -> str:
    try:
        async with s.get(url, timeout=cfg.timeout, allow_redirects=True) as r:
            if r.status == 404: return "нет"
            if "/login" in str(r.url) or "/signup" in str(r.url): return "нет (редирект)"
            if r.status == 200:
                if login_check:
                    text = (await r.text(errors="ignore"))[:20000].lower()
                    if any(m in text for m in NOT_FOUND_MARKERS): return "нет"
                return "есть"
            return f"HTTP {r.status}"
    except Exception as e:
        return f"ошибка: {type(e).__name__}"

async def _run(query: str, **_):
    nick = query.strip().lstrip("@")
    out = [f"Ник «{nick}» (быстрая проверка):"]
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
    async with aiohttp.ClientSession(headers=headers) as s:
        for name, tpl, login_check in CHECKS:
            status = await _check(s, tpl.format(u=nick), login_check)
            out.append(f"  {name}: {status}")
    return "\n".join(out)

plugin("social", "Быстрая проверка 5 площадок по нику", ("nick",))(_run)
