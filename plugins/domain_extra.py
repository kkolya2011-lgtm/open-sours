import asyncio
import aiohttp
import dns.resolver
from registry import plugin
from config import cfg

async def _txt(domain: str, name: str) -> list[str]:
    try:
        ans = await asyncio.to_thread(dns.resolver.resolve, name, "TXT", lifetime=5)
        return [str(r) for r in ans]
    except Exception:
        return []

async def _run(query: str, **_):
    d = query.strip().lower()
    out = [f"Domain extra {d}:"]
    mx = []
    try:
        ans = await asyncio.to_thread(dns.resolver.resolve, d, "MX", lifetime=5)
        mx = sorted(str(r.exchange) for r in ans)
    except Exception:
        pass
    out.append(f"  MX: {', '.join(mx) if mx else '—'}")
    
    spf = [t for t in await _txt(d, d) if "v=spf1" in t]
    dmarc = [t for t in await _txt(d, f"_dmarc.{d}") if "v=DMARC1" in t]
    out.append(f"  SPF: {'да' if spf else 'нет'}")
    out.append(f"  DMARC: {'да' if dmarc else 'нет'}")
    
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://{d}", timeout=cfg.timeout, allow_redirects=True) as r:
                out.append(f"  HTTPS: {r.status} → {r.url}")
    except Exception as e:
        out.append(f"  HTTPS: ошибка {type(e).__name__}")
    return "\n".join(out)

plugin("domain_extra", "MX/SPF/DMARC/HTTPS по домену", ("domain",))(_run)
