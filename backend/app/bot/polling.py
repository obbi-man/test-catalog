"""Локальная разработка: python -m app.bot.polling (BOT_MODE=polling). Для продакшена не нужен."""
import asyncio

from aiogram import Bot

from app.bot.handlers import build_dispatcher
from app.config import get_settings
from app.db import make_engine, make_session_factory
from app.services.storage import S3Storage


async def main():
    s = get_settings()
    bot = Bot(s.bot_token)
    await bot.delete_webhook()
    dp = build_dispatcher(
        admin_ids=s.admin_id_set, webapp_url=s.webapp_url,
        session_factory=make_session_factory(make_engine()),
        storage=S3Storage(s), max_image_bytes=s.max_image_bytes,
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
