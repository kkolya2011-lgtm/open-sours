import re
import aiohttp
from registry import plugin
from config import cfg

RE_VIN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$", re.I)

async def _run(query: str, **_):
    vin = query.strip().upper()
    if not RE_VIN.fullmatch(vin): return f"vin_decode: «{query}» не VIN"
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=cfg.timeout) as r:
                data = await r.json()
        results = (data.get("Results") or [{}])[0]
        out = [f"VIN {vin}:"]
        for k in ("Make", "Model", "ModelYear", "BodyClass", "VehicleType"):
            if results.get(k): out.append(f"  {k}: {results[k]}")
        return "\n".join(out)
    except Exception as e:
        return f"vin_decode: ошибка {type(e).__name__}"

plugin("vin_decode", "Расшифровка VIN (NHTSA)", ("vin",))(_run)
