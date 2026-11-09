import aiohttp
from registry import plugin
from config import cfg

async def _fetch(s: aiohttp.ClientSession, url: str) -> str | None:
    try:
        async with s.get(url, timeout=cfg.timeout, allow_redirects=True) as r:
            if r.status == 200:
                return (await r.text(errors="ignore"))[:5000]
    except Exception:
        pass
    return None

async def _run(query: str, **_):
    domain = query.strip().lower()
    base = f"https://{domain}"
    out = [f"robots/sitemap {domain}:"]
    async with aiohttp.ClientSession() as s:
        robots = await _fetch(s, f"{base}/robots.txt")
        if robots:
            lines = [ln for ln in robots.splitlines() if ln.strip()][:15]
            out.append("  robots.txt:")
            out.extend(f"    {ln}" for ln in lines)
        else:
            out.append("  robots.txt: нет/недоступен")

        sitemap = await _fetch(s, f"{base}/sitemap.xml")
        if sitemap:
            import re
            locs = re.findall(r"<loc>(.*?)</loc>", sitemap)
            out.append(f"  sitemap.xml: {len(locs)} URL")
            for loc in locs[:10]: out.append(f"    {loc}")
            if len(locs) > 10: out.append(f"    … ещё {len(locs) - 10}")
        else:
            out.append("  sitemap.xml: нет/недоступен")
    return "\n".join(out)

plugin("robots", "robots.txt и sitemap.xml по домену", ("domain",))(_run)
