import hashlib
import aiohttp
from registry import plugin
from config import cfg

async def _run(query: str, **_):
    email = query.strip().lower()
    h = hashlib.md5(email.encode()).hexdigest()
    url = f"https://www.gravatar.com/{h}.json"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=cfg.timeout) as r:
                if r.status == 404: return f"Gravatar {email}: профиля нет"
                if r.status != 200: return f"Gravatar: HTTP {r.status}"
                data = await r.json()
    except Exception as e:
        return f"Gravatar: ошибка {type(e).__name__}"

    entry = (data.get("entry") or [{}])[0]
    out = [f"Gravatar {email}:"]
    for k in ("displayName", "preferredUsername", "aboutMe", "location", "profileUrl"):
        if entry.get(k): out.append(f"  {k}: {entry[k]}")
    name = entry.get("name") or {}
    if name.get("formatted"): out.append(f"  name: {name['formatted']}")
    accounts = entry.get("accounts") or []
    if accounts:
        out.append("  accounts:")
        for a in accounts[:10]:
            out.append(f"    - {a.get('shortname', '?')}: {a.get('url', '')}")
    return "\n".join(out)

plugin("gravatar", "Профиль Gravatar по email", ("email",))(_run)
