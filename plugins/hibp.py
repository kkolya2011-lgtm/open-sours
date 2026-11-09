import aiohttp
from registry import plugin
from config import cfg

async def _run(query: str, **_):
    if not cfg.hibp_key:
        return "HIBP: API-ключ не задан (HIBP_API_KEY)"
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{query}"
    headers = {"hibp-api-key": cfg.hibp_key, "user-agent": "osintbot"}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers, timeout=cfg.timeout, params={"truncateResponse": "false"}) as r:
            if r.status == 404: return f"HIBP: {query} не найден в утечках"
            if r.status != 200: return f"HIBP: HTTP {r.status}"
            data = await r.json()
    lines = [f"HIBP {query}: {len(data)} утечек"]
    for b in data[:20]:
        lines.append(f"  - {b['Name']} ({b.get('BreachDate', '?')}), типы: {', '.join(b.get('DataClasses', []))}")
    return "\n".join(lines)

plugin("hibp", "Проверка email в HaveIBeenPwned", ("email",))(_run)
