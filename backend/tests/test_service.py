import pytest

from app.repositories.products import ProductRepository
from app.services.products import ProductError, ProductService


async def test_create_stores_image_and_record(session_factory, storage):
    async with session_factory() as s:
        svc = ProductService(ProductRepository(s), storage, 100)
        p = await svc.create("  Лампа ", b"abc", "image/png")
    assert p.name == "Лампа"
    assert storage.objects[p.image_key] == (b"abc", "image/png")


@pytest.mark.parametrize("name,img", [("", b"x"), ("   ", b"x"), ("a" * 300, b"x"), ("ok", b""), ("ok", b"x" * 101)])
async def test_validation(session_factory, storage, name, img):
    async with session_factory() as s:
        svc = ProductService(ProductRepository(s), storage, 100)
        with pytest.raises(ProductError):
            await svc.create(name, img)
    assert storage.objects == {}
