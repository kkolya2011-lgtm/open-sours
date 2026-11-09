import aiohttp
import re
from registry import plugin
from config import cfg

RE_PLATE = re.compile(r"^[АВЕКМНОРСТУХABEKMHOPCTYX]\d{3}[АВЕКМНОРСТУХABEKMHOPCTYX]{2}\d{2,3}$", re.I)

def _normalize(plate: str) -> str:
    return re.sub(r"[\s-]", "", plate.strip().upper())

async def _mentions(plate: str) -> str:
    if not cfg.serper_key: return "  mentions: SERPER_KEY не задан"
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": cfg.serper_key, "Content-Type": "application/json"}
    payload = {"q": f'"{plate}"', "num": 5}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, headers=headers, json=payload, timeout=cfg.timeout) as r:
                data = await r.json()
        items = data.get("organic", []) or []
        if not items: return "  mentions: ничего"
        out = ["  mentions:"]
        for it in items: out.append(f"    - {it.get('title')}\n      {it.get('link')}")
        return "\n".join(out)
    except Exception:
        return "  mentions: ошибка"

async def _run(query: str, **_):
    plate = _normalize(query)
    if not RE_PLATE.fullmatch(plate): return f"plate_intel: «{query}» не госномер"
    out = [f"Plate {plate}:"]
    out.append(await _mentions(plate))
    out.append(f"  autocode: https://autocode.ru/check/?q={plate}")
    return "\n".join(out)

plugin("plate_intel", "Поиск по госномеру", ("plate",))(_run)
