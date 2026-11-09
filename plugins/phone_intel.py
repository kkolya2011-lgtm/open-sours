import aiohttp
import re
from registry import plugin
from config import cfg

RE_PHONE = re.compile(r"^\+?\d{10,15}$")

def _normalize(phone: str) -> str:
    return re.sub(r"[^\d+]", "", phone.strip())

async def _numverify(phone: str) -> str:
    if not cfg.numverify_key:
        return "  numverify: ключ не задан"
    url = "http://apilayer.net/api/validate"
    params = {"access_key": cfg.numverify_key, "number": phone, "format": "1"}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params, timeout=cfg.timeout) as r:
                data = await r.json()
                if not data.get("valid"): return "  numverify: невалиден"
                return f"  numverify: {data.get('country_name')}, {data.get('location')}, {data.get('carrier')}, {data.get('line_type')}"
    except Exception:
        return "  numverify: ошибка"

async def _mentions(phone: str) -> str:
    if not cfg.serper_key: return "  mentions: SERPER_KEY не задан"
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": cfg.serper_key, "Content-Type": "application/json"}
    payload = {"q": f'"{phone}"', "num": 5}
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
    phone = _normalize(query)
    if not RE_PHONE.fullmatch(phone): return f"phone_intel: «{query}» не номер"
    out = [f"Phone {phone}:"]
    out.append(await _numverify(phone))
    out.append(await _mentions(phone))
    return "\n".join(out)

plugin("phone_intel", "Инфо по номеру телефона", ("phone",))(_run)
