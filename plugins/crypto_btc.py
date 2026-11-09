import re
import aiohttp
from registry import plugin
from config import cfg

RE_BTC = re.compile(r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$")

async def _run(query: str, **_):
    addr = query.strip()
    if not RE_BTC.fullmatch(addr): return f"btc: «{addr}» не BTC-адрес"
    base = "https://blockchain.info"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{base}/rawaddr/{addr}?limit=5", timeout=cfg.timeout) as r:
                data = await r.json()
        out = [f"BTC {addr}:"]
        out.append(f"  balance: {data.get('final_balance', 0) / 1e8:.8f} BTC")
        out.append(f"  total_received: {data.get('total_received', 0) / 1e8:.8f} BTC")
        out.append(f"  txs: {data.get('n_tx', 0)}")
        return "\n".join(out)
    except Exception as e:
        return f"btc: ошибка {type(e).__name__}"

plugin("crypto_btc", "Баланс/транзакции BTC", ("btc",))(_run)
