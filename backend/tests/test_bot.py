from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.types import Message

from app.bot.handlers import build_dispatcher
from app.repositories.products import ProductRepository


def make_update(user_id, *, text=None, caption=None, photo=False):
    from aiogram.types import Update

    msg = {
        "message_id": 1, "date": 0, "chat": {"id": user_id, "type": "private"},
        "from": {"id": user_id, "is_bot": False, "first_name": "T"},
    }
    if text:
        msg["text"] = text
    if photo:
        msg["photo"] = [
            {"file_id": "small", "file_unique_id": "a", "width": 10, "height": 10},
            {"file_id": "big", "file_unique_id": "b", "width": 100, "height": 100},
        ]
    if caption:
        msg["caption"] = caption
    return Update.model_validate({"update_id": 1, "message": msg})


def make_bot():
    bot = AsyncMock()
    bot.id = 42

    async def download(photo, destination):
        destination.write(b"PHOTO-BYTES")

    bot.download.side_effect = download
    return bot


async def run(update, bot, session_factory, storage):
    dp = build_dispatcher(admin_ids={1}, webapp_url="https://app.test", session_factory=session_factory,
                          storage=storage, max_image_bytes=1000)
    # Message.answer использует bot из контекста; подменяем на мок
    update.message._bot = bot
    answers = []

    async def answer(self, text, **kw):
        answers.append((text, kw))

    Message.answer = answer
    await dp.feed_update(bot, update)
    return answers


async def test_non_admin_gets_webapp_button(session_factory, storage):
    ans = await run(make_update(5, text="/start"), make_bot(), session_factory, storage)
    assert ans[0][0] == "У меня есть товар"
    btn = ans[0][1]["reply_markup"].inline_keyboard[0][0]
    assert btn.web_app.url == "https://app.test"


async def test_non_admin_photo_does_not_create_product(session_factory, storage):
    ans = await run(make_update(5, caption="X", photo=True), make_bot(), session_factory, storage)
    assert ans[0][0] == "У меня есть товар"
    assert storage.objects == {}


async def test_admin_photo_creates_product(session_factory, storage):
    ans = await run(make_update(1, caption="Чайник", photo=True), make_bot(), session_factory, storage)
    assert "создан" in ans[0][0]
    assert len(storage.objects) == 1
    assert list(storage.objects.values())[0][0] == b"PHOTO-BYTES"
    async with session_factory() as s:
        items = await ProductRepository(s).list()
    assert [p.name for p in items] == ["Чайник"]


async def test_admin_photo_without_caption(session_factory, storage):
    ans = await run(make_update(1, photo=True), make_bot(), session_factory, storage)
    assert "подпись" in ans[0][0]
    assert storage.objects == {}


async def test_admin_create_command(session_factory, storage):
    ans = await run(make_update(1, text="Создать товар"), make_bot(), session_factory, storage)
    assert "фото" in ans[0][0]
