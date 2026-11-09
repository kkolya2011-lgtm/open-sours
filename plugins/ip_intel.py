import aiohttp
from registry import plugin
from config import cfg

async def _run(query: str, **_):
    q = query.strip()
    url = f"https://ipinfo.io/{q}/json"
    params = {}
    if cfg.ipinfo_token:
        params["token"] = cfg.ipinfo_token
    async with aiohttp.ClientSession() as s:
        async with s.get(url, params=params, timeout=cfg.timeout) as r:
            if r.status != 200:
                return f"ipinfo: HTTP {r.status}"
            data = await r.json()
    keys = ("ip", "hostname", "city", "region", "country", "org", "timezone")
    out = [f"IP {q}:"]
    for k in keys:
        if data.get(k):
            out.append(f"  {k}: {data[k]}")
    return "\n".join(out)

plugin("ip_intel", "Гео/ASN по IP (ipinfo.io)", ("ip",))(_run)
