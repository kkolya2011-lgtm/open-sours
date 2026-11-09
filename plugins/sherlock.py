import asyncio
import aiohttp
from registry import plugin
from config import cfg

SITES: list[tuple[str, str, tuple[str, ...]]] = [
    ("GitHub",      "https://github.com/{u}",                     ("Not Found",)),
    ("GitLab",      "https://gitlab.com/{u}",                     ("Page Not Found",)),
    ("Reddit",      "https://www.reddit.com/user/{u}/about.json", ('"error": 404',)),
    ("VK",          "https://vk.com/{u}",                         ("page not found",)),
    ("OK",          "https://ok.ru/{u}",                          ("not found",)),
    ("Instagram",   "https://www.instagram.com/{u}/",             ("Sorry, this page isn't available",)),
    ("TikTok",      "https://www.tiktok.com/@{u}",                ("Couldn't find this account",)),
    ("Twitter/X",   "https://x.com/{u}",                          ("This account doesn’t exist",)),
    ("YouTube",     "https://www.youtube.com/@{u}",               ("This page isn't available",)),
    ("Twitch",      "https://www.twitch.tv/{u}",                  ("page not found",)),
    ("Steam",       "https://steamcommunity.com/id/{u}",          ("The specified profile could not be found",)),
    ("Pinterest",   "https://www.pinterest.com/{u}/",             ("Page not found",)),
    ("SoundCloud",  "https://soundcloud.com/{u}",                 ("We can't find that user",)),
    ("Behance",     "https://www.behance.net/{u}",                ("Page Not Found",)),
    ("Dribbble",    "https://dribbble.com/{u}",                   ("Page not found",)),
    ("Flickr",      "https://www.flickr.com/people/{u}",          ("Page Not Found",)),
    ("Habr",        "https://habr.com/ru/users/{u}/",             ("Страница не найдена",)),
    ("Pikabu",      "https://pikabu.ru/@{u}",                     ("Страница не найдена",)),
    ("Yandex.Zen",  "https://dzen.ru/{u}",                        ("Страница не найдена",)),
    ("LiveJournal", "https://{u}.livejournal.com",                ("Unknown journal",)),
    ("Last.fm",     "https://www.last.fm/user/{u}",               ("Page not found",)),
    ("Patreon",     "https://www.patreon.com/{u}",                ("Page not found",)),
    ("Keybase",     "https://keybase.io/{u}",                     ("Page not found",)),
    ("HackerNews",  "https://news.ycombinator.com/user?id={u}",   ("No such user",)),
    ("ProductHunt", "https://www.producthunt.com/@{u}",           ("Page not found",)),
]

_semaphore = asyncio.Semaphore(cfg.sherlock_concurrency)

async def _check(s: aiohttp.ClientSession, name: str, url: str, markers: tuple[str, ...]) -> str:
    async with _semaphore:
        try:
            async with s.get(url, timeout=cfg.timeout, allow_redirects=True) as r:
                if r.status == 404: return "нет"
                if "/login" in str(r.url) or "/signup" in str(r.url): return "нет (редирект)"
                if r.status != 200: return f"HTTP {r.status}"
                if not markers: return "есть"
                text = (await r.text(errors="ignore"))[:20000]
                if any(m in text for m in markers): return "нет"
                return "есть"
        except asyncio.TimeoutError:
            return "таймаут"
        except Exception as e:
            return f"ошибка: {type(e).__name__}"

async def _run(query: str, **_):
    nick = query.strip().lstrip("@")
    if not nick: return "sherlock: пустой ник"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    async with aiohttp.ClientSession(headers=headers) as s:
        tasks = [_check(s, name, tpl.format(u=nick), markers) for name, tpl, markers in SITES]
        results = await asyncio.gather(*tasks)

    found, missing, errors = [], [], []
    for (name, _, _), status in zip(SITES, results):
        if status == "есть": found.append(name)
        elif status == "нет": missing.append(name)
        else: errors.append(f"{name}: {status}")

    out = [f"Sherlock «{nick}» (площадок: {len(SITES)}):"]
    out.append(f"  найдено ({len(found)}): {', '.join(found) if found else '—'}")
    out.append(f"  не найдено ({len(missing)}): {', '.join(missing) if missing else '—'}")
    if errors: out.append(f"  проблемы ({len(errors)}): {'; '.join(errors[:8])}")
    return "\n".join(out)

plugin("sherlock", "Проверка ника по 25+ площадкам", ("nick",))(_run)
