from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from starlette.concurrency import iterate_in_threadpool

from app.deps import get_product_service, get_storage
from app.schemas import ProductOut
from app.services.products import ProductService
from app.services.storage import Storage

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
async def list_products(service: ProductService = Depends(get_product_service)):
    items = await service.list()
    return [
        ProductOut(id=p.id, name=p.name, image_url=f"/api/products/{p.id}/image", created_at=p.created_at)
        for p in items
    ]


@router.get("/{product_id}/image")
async def product_image(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    storage: Storage = Depends(get_storage),
):
    product = await service.repo.get(product_id)
    if product is None:
        raise HTTPException(404, "Товар не найден")
    try:
        chunks, content_type = storage.open(product.image_key)
    except KeyError:
        raise HTTPException(404, "Изображение не найдено")
    return StreamingResponse(
        iterate_in_threadpool(chunks),
        media_type=product.content_type or content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
