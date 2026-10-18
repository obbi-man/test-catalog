import io
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.repositories.products import ProductRepository
from app.services.products import ProductError, ProductService

log = logging.getLogger(__name__)

CREATE_HELP = (
    "Чтобы создать товар, отправьте ОДНО сообщение: фото + подпись. "
    "Подпись будет названием товара."
)


def build_router(*, admin_ids: set[int], webapp_url: str, session_factory, storage, max_image_bytes: int) -> Router:
    router = Router()

    def is_admin(message: Message) -> bool:
        return message.from_user is not None and message.from_user.id in admin_ids

    @router.message(Command("create"), F.func(is_admin))
    @router.message(F.text == "Создать товар", F.func(is_admin))
    async def create_help(message: Message):
        await message.answer(CREATE_HELP)

    @router.message(F.photo, F.func(is_admin))
    async def admin_photo(message: Message, bot: Bot):
        name = (message.caption or "").strip()
        if not name:
            await message.answer("Добавьте подпись к фото: она станет названием товара.")
            return
        photo = message.photo[-1]  # самое большое разрешение
        buf = io.BytesIO()  # только память, на диск ничего не пишем
        await bot.download(photo, destination=buf)
        async with session_factory() as session:
            service = ProductService(ProductRepository(session), storage, max_image_bytes)
            try:
                product = await service.create(name, buf.getvalue(), "image/jpeg")
            except ProductError as e:
                await message.answer(str(e))
                return
        await message.answer(f"Товар «{product.name}» создан (id={product.id}).")

    @router.message(F.func(is_admin))
    async def admin_other(message: Message):
        await message.answer(CREATE_HELP)

    @router.message()
    async def anyone(message: Message):
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Открыть каталог", web_app=WebAppInfo(url=webapp_url))]]
        )
        await message.answer("У меня есть товар", reply_markup=kb)

    return router


def build_dispatcher(**kwargs) -> Dispatcher:
    dp = Dispatcher()  # MemoryStorage FSM не используется: бот не хранит состояние диалогов
    dp.include_router(build_router(**kwargs))
    return dp
