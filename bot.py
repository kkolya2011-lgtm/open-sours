import asyncio
import logging
import re

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import cfg
import cache
import ratelimit
import plugins  # noqa: F401 — регистрация плагинов при импорте
from registry import REGISTRY, for_kind

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("bot")

bot = Bot(cfg.bot_token)
dp = Dispatcher()

# ---------- определение типа входа ----------

def detect_kind(q: str) -> str | None:
    q = q.strip()
    # координаты "lat,lon"
    m = re.fullmatch(r"(-?\d{1,3}(?:\.\d+)?)\s*[, ]\s*(-?\d{1,3}(?:\.\d+)?)", q)
    if m:
        return "coords"
    # BTC
    if re.fullmatch(r"(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}", q):
        return "btc"
    # VIN (17 символов, без I/O/Q)
    if re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", q.upper()):
        return "vin"
    # хэш md5/sha1/sha256
    if re.fullmatch(r"[a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64}", q):
        return "hash"
    # IP
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", q):
        return "ip"
    # email
    if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", q):
        return "email"
    # @username
    if q.startswith("@"):
        return "username"
    # домен
    if re.fullmatch(r"(?:[a-z0-9-]+\.)+[a-z]{2,}", q.lower()) and " " not in q:
        return "domain"
    # ФИО (2–4 слова с заглавной)
    if re.fullmatch(r"(?:[А-ЯЁA-Z][а-яёa-z-]+\s+){1,3}[А-ЯЁA-Z][а-яёa-z-]+", q):
        return "name"
    # госномер РФ
    if re.fullmatch(
        r"[АВЕКМНОРСТУХABEKMHOPCTYX]\d{3}[АВЕКМНОРСТУХABEKMHOPCTYX]{2}\d{2,3}",
        re.sub(r"[\s-]", "", q.upper()),
    ):
        return "plate"
    # телефон
    if re.fullmatch(r"\+?\d{10,15}", re.sub(r"[^\d+]", "", q)):
        return "phone"
    # ник
    if re.fullmatch(r"[A-Za-zА-Яа-я0-9_.-]{2,64}", q):
        return "nick"
    return None

# ---------- извлечение связанных сущностей ----------

RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
RE_DOMAIN = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b")

def extract_artifacts(text: str) -> dict[str, set[str]]:
    return {
        "email": set(RE_EMAIL.findall(text)),
        "ip": set(RE_IP.findall(text)),
        "domain": {d.lower() for d in RE_DOMAIN.findall(text)},
    }

def merge_artifacts(acc: dict[str, set[str]], new: dict[str, set[str]]) -> None:
    for k, v in new.items():
        acc[k].update(v)

def format_artifacts(acc: dict[str, set[str]], exclude: str | None = None) -> str:
    exclude = (exclude or "").lower()
    lines = ["Связанные сущности:"]
    for kind in ("email", "ip", "domain"):
        items = sorted(x for x in acc[kind] if x.lower() != exclude)
        if items:
            lines.append(f"  {kind}: {', '.join(items[:15])}")
    return "\n".join(lines) if len(lines) > 1 else ""

# ---------- Telegram handlers ----------

@dp.message(CommandStart())
async def cmd_start(m: Message):
    names = ", ".join(sorted(REGISTRY))
    await m.answer(
        "OSINT-бот (только публичные источники).\n\n"
        "Пришли: домен, IP, email, @username, ник, ФИО, номер, госномер, VIN, координаты, BTC-адрес или хэш.\n"
        f"Плагины: {names}\n\n"
        "/id — твой Telegram ID\n"
        "/cleanup — очистить устаревший кэш"
    )

@dp.message(Command("id"))
async def cmd_id(m: Message):
    await m.answer(f"user id: {m.from_user.id}\nchat id: {m.chat.id}")

@dp.message(Command("cleanup"))
async def cmd_cleanup(m: Message):
    removed = await cache.cleanup(cfg.cache_ttl)
    await m.answer(f"Удалено устаревших записей кэша: {removed}")

@dp.message(F.text & ~F.text.startswith("/"))
async def handle(m: Message):
    if not ratelimit.allow(m.from_user.id, cfg.rate_limit):
        return await m.answer("Слишком часто, подожди.")

    q = m.text.strip()
    kind = detect_kind(q)
    if not kind:
        return await m.answer("Не понял формат. Домен/IP/email/@user/ник/ФИО/номер?")

    targets = for_kind(kind)
    if not targets:
        return await m.answer(f"Нет плагинов для типа «{kind}»")

    await m.answer(f"Тип: {kind}. Запускаю {len(targets)} плагин(ов)…")

    artifacts: dict[str, set[str]] = {"email": set(), "ip": set(), "domain": set()}
    for p in targets:
        cached = await cache.get(p.name, q, cfg.cache_ttl)
        if cached is not None:
            await m.answer(f"[{p.name}] (кэш)\n{cached}")
            merge_artifacts(artifacts, extract_artifacts(cached))
            continue

        try:
            result = await p.handler(bot=bot, query=q)
        except Exception as e:
            result = f"[{p.name}] ошибка: {type(e).__name__}: {e}"

        if not isinstance(result, str):
            result = str(result)
        if len(result) > 3500:
            result = result[:3500] + "\n…(обрезано)"

        await cache.put(p.name, q, result)
        await m.answer(f"[{p.name}]\n{result}")
        merge_artifacts(artifacts, extract_artifacts(result))

    summary = format_artifacts(artifacts, exclude=q if kind in ("domain", "email", "ip") else None)
    if summary:
        if len(summary) > 3500:
            summary = summary[:3500] + "\n…(обрезано)"
        await m.answer(summary)

# ---------- запуск ----------

async def main():
    if not cfg.bot_token:
        raise SystemExit("BOT_TOKEN не задан")
    await cache.init()
    log.info("plugins: %s", ", ".join(sorted(REGISTRY)))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
