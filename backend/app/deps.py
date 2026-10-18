from typing import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.products import ProductRepository
from app.services.products import ProductService
from app.services.storage import Storage


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


def get_storage(request: Request) -> Storage:
    return request.app.state.storage


def get_product_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
    storage: Storage = Depends(get_storage),
) -> ProductService:
    return ProductService(ProductRepository(session), storage, request.app.state.settings.max_image_bytes)
