from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, name: str, image_key: str, content_type: str) -> Product:
        product = Product(name=name, image_key=image_key, content_type=content_type)
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def list(self) -> list[Product]:
        res = await self.session.execute(select(Product).order_by(Product.id.desc()))
        return list(res.scalars())

    async def get(self, product_id: int) -> Product | None:
        return await self.session.get(Product, product_id)
