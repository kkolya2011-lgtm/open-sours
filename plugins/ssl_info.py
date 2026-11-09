import asyncio
import ssl
import socket
from registry import plugin

def _get_cert(domain: str) -> dict:
    ctx = ssl.create_default_context()
    with socket.create_connection((domain, 443), timeout=10) as sock:
        with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
            return ssock.getpeercert()

async def _run(query: str, **_):
    domain = query.strip().lower()
    try:
        cert = await asyncio.to_thread(_get_cert, domain)
    except Exception as e:
        return f"SSL {domain}: ошибка {type(e).__name__}: {e}"

    out = [f"SSL {domain}:"]
    issuer = {k: v for t in cert.get("issuer", ()) for k, v in t}
    subject = {k: v for t in cert.get("subject", ()) for k, v in t}
    if issuer.get("organizationName"): out.append(f"  issuer: {issuer['organizationName']}")
    if subject.get("commonName"): out.append(f"  subject CN: {subject['commonName']}")
    out.append(f"  notBefore: {cert.get('notBefore')}")
    out.append(f"  notAfter: {cert.get('notAfter')}")
    sans = [v for k, v in cert.get("subjectAltName", ()) if k == "DNS"]
    if sans:
        out.append(f"  SAN ({len(sans)}):")
        for s in sans[:25]: out.append(f"    - {s}")
        if len(sans) > 25: out.append(f"    … ещё {len(sans) - 25}")
    return "\n".join(out)

plugin("ssl_info", "SSL-сертификат по домену (issuer, срок, SAN)", ("domain",))(_run)
