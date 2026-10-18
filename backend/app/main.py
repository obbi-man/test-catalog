import logging
from contextlib import asynccontextmanager

from aiogram import Bot
from fastapi import FastAPI

from app.bot.handlers import build_dispatcher
from app.config import Settings, get_settings
from app.db import make_engine, make_session_factory
from app.routers import bot as bot_router
from app.routers import health, products
from app.services.storage import S3Storage

log = logging.getLogger("catalog")


def create_app(settings: Settings | None = None, *, storage=None, session_factory=None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = None
        if session_factory is None:
            engine = make_engine(settings.database_url)
            app.state.session_factory = make_session_factory(engine)
        else:
            app.state.session_factory = session_factory
        app.state.storage = storage or S3Storage(settings)
        app.state.settings = settings
        app.state.bot = app.state.dp = None
        if settings.bot_token and settings.bot_mode != "off":
            app.state.bot = Bot(settings.bot_token)
            app.state.dp = build_dispatcher(
                admin_ids=settings.admin_id_set, webapp_url=settings.webapp_url,
                session_factory=app.state.session_factory, storage=app.state.storage,
                max_image_bytes=settings.max_image_bytes,
            )
            if settings.bot_mode == "webhook" and settings.webhook_base_url:
                # Идемпотентно: все реплики ставят один и тот же URL.
                url = f"{settings.webhook_base_url.rstrip('/')}/bot/webhook/{settings.webhook_secret}"
                try:
                    await app.state.bot.set_webhook(url, secret_token=settings.webhook_secret)
                except Exception:  # не валим сервис, если Telegram временно недоступен
                    log.exception("set_webhook failed")
        yield
        if app.state.bot:
            await app.state.bot.session.close()
        if engine:
            await engine.dispose()

    app = FastAPI(title="Catalog", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(products.router)
    app.include_router(bot_router.router)
    return app


app = create_app()
