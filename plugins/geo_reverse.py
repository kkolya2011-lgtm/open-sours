import aiohttp
from registry import plugin
from config import cfg

async def _run(query: str, **_):
    q = query.strip()
    lat, lon = None, None
    for sep in (",", " "):
        if sep in q:
            parts = [p.strip() for p in q.split(sep, 1)]
            if len(parts) == 2:
                try:
                    lat, lon = float(parts[0]), float(parts[1])
                    break
                except ValueError: continue
    if lat is None: return f"geo_reverse: «{q}» не координаты"

    url = "https://nominatim.openstreetmap.org/reverse"
    headers = {"User-Agent": "osintbot/1.0"}
    params = {"lat": lat, "lon": lon, "format": "json", "addressdetails": "1"}
    try:
        async with aiohttp.ClientSession(headers=headers) as s:
            async with s.get(url, params=params, timeout=cfg.timeout) as r:
                data = await r.json()
        out = [f"Geo {lat},{lon}:"]
        if data.get("display_name"): out.append(f"  address: {data['display_name']}")
        return "\n".join(out)
    except Exception as e:
        return f"geo_reverse: ошибка {type(e).__name__}"

plugin("geo_reverse", "Reverse geocode (Nominatim)", ("coords",))(_run)
