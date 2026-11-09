import aiohttp
from registry import plugin
from config import cfg

async def _run(query: str, **_):
    email = query.strip()
    headers = {"User-Agent": "osintbot"}
    if cfg.emailrep_key: headers["Key"] = cfg.emailrep_key
    url = f"https://emailrep.io/{email}"
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers, timeout=cfg.timeout) as r:
            if r.status == 429: return "emailrep: лимит запросов"
            if r.status != 200: return f"emailrep: HTTP {r.status}"
            data = await r.json()
    out = [f"EmailRep {email}:"]
    for k in ("reputation", "suspicious", "references", "blacklisted"):
        v = data.get(k)
        if v not in (None, "", [], {}): out.append(f"  {k}: {v}")
    details = data.get("details") or {}
    if details:
        out.append("  details:")
        for kk, vv in details.items():
            if vv not in (None, "", [], {}, False): out.append(f"    {kk}: {vv}")
    return "\n".join(out)

plugin("emailrep", "Репутация email (emailrep.io)", ("email",))(_run)
