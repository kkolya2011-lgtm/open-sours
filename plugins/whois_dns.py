import asyncio
import aiohttp
import dns.resolver
import whois
from registry import plugin
from config import cfg

def _whois_sync(domain: str) -> str:
    try:
        w = whois.whois(domain)
        parts = []
        for k in ("registrar", "creation_date", "expiration_date", "name_servers", "org", "country"):
            v = w.get(k)
            if v: parts.append(f"  {k}: {v}")
        return "\n".join(parts) or "  (пусто)"
    except Exception as e:
        return f"  whois error: {type(e).__name__}: {e}"

async def _dns(domain: str) -> list[str]:
    res = []
    for rtype in ("A", "AAAA", "MX", "NS", "TXT"):
        try:
            ans = await asyncio.to_thread(dns.resolver.resolve, domain, rtype, lifetime=5)
            vals = ", ".join(str(r) for r in ans)
            res.append(f"  {rtype}: {vals}")
        except Exception:
            pass
    return res

async def _crtsh(domain: str) -> list[str]:
    names: set[str] = set()
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://crt.sh/?q=%25.{domain}&output=json", timeout=cfg.timeout) as r:
                if r.status == 200:
                    data = await r.json(content_type=None)
                    for row in data:
                        for n in row.get("name_value", "").split("\n"):
                            n = n.strip()
                            if n: names.add(n)
    except Exception:
        pass
    return sorted(names)[:25]

async def _run(query: str, **_):
    domain = query.strip().lower()
    whois_part = await asyncio.to_thread(_whois_sync, domain)
    dns_part = await _dns(domain)
    out = [f"WHOIS {domain}:", whois_part, "DNS:"]
    out.extend(dns_part or ["  (нет записей)"])
    subs = await _crtsh(domain)
    if subs:
        out.append("crt.sh subdomains:")
        out.extend(f"  {n}" for n in subs)
    return "\n".join(out)

plugin("whois_dns", "WHOIS + DNS + crt.sh по домену", ("domain",))(_run)
