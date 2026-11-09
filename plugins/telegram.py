from registry import plugin
from aiogram import Bot

async def _run(bot: Bot, query: str, **_):
    username = query.lstrip("@")
    try:
        chat = await bot.get_chat(f"@{username}")
    except Exception as e:
        return f"Telegram: не удалось получить @{username} ({type(e).__name__}: {e})"
    lines = [f"Telegram @{username}:"]
    if chat.full_name: lines.append(f"  имя: {chat.full_name}")
    if chat.username: lines.append(f"  username: @{chat.username}")
    lines.append(f"  id: {chat.id}")
    lines.append(f"  тип: {chat.type}")
    if getattr(chat, "bio", None):
        lines.append(f"  bio: {chat.bio}")
    return "\n".join(lines)

plugin("telegram", "Публичный профиль Telegram по username", ("username",))(_run)
