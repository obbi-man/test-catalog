import io
from typing import Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.db import Base, make_session_factory
from app.main import create_app
import app.models  # noqa: F401


class FakeStorage:
    """Подмена MinIO: хранит объекты в словаре в памяти."""

    def __init__(self):
        self.objects: dict[str, tuple[bytes, str]] = {}

    async def put(self, key, data, content_type):
        self.objects[key] = (data, content_type)

    def open(self, key) -> tuple[Iterator[bytes], str]:
        if key not in self.objects:
            raise KeyError(key)
        data, ct = self.objects[key]
        return iter([data[:3], data[3:]]), ct

    async def ping(self):
        pass


@pytest.fixture
def settings():
    return Settings(bot_token="", admin_ids="1,2", webhook_secret="s3cret", webapp_url="https://x.test")


@pytest.fixture
def storage():
    return FakeStorage()


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield make_session_factory(engine)
    await engine.dispose()


@pytest.fixture
async def client(settings, storage, session_factory):
    app = create_app(settings, storage=storage, session_factory=session_factory)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            yield c
