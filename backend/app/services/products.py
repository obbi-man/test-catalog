import uuid

from app.repositories.products import ProductRepository
from app.services.storage import Storage


class ProductError(ValueError):
    pass


class ProductService:
    def __init__(self, repo: ProductRepository, storage: Storage, max_image_bytes: int):
        self.repo = repo
        self.storage = storage
        self.max_image_bytes = max_image_bytes

    async def create(self, name: str, image: bytes, content_type: str = "image/jpeg"):
        name = (name or "").strip()
        if not name:
            raise ProductError("Название товара пустое")
        if len(name) > 255:
            raise ProductError("Название слишком длинное (макс. 255 символов)")
        if not image:
            raise ProductError("Пустое изображение")
        if len(image) > self.max_image_bytes:
            raise ProductError("Изображение слишком большое")
        # Сначала файл, потом запись: при сбое останется только «осиротевший» объект, не битая запись.
        key = f"products/{uuid.uuid4().hex}"
        await self.storage.put(key, image, content_type)
        return await self.repo.add(name, key, content_type)

    async def list(self):
        return await self.repo.list()
