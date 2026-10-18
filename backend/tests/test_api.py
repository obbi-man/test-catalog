async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


async def test_empty_list(client):
    r = await client.get("/api/products")
    assert r.status_code == 200 and r.json() == []


async def test_image_404(client):
    assert (await client.get("/api/products/999/image")).status_code == 404


async def test_list_and_image_stream(client, session_factory, storage):
    from app.repositories.products import ProductRepository
    from app.services.products import ProductService

    async with session_factory() as s:
        svc = ProductService(ProductRepository(s), storage, 1000)
        p = await svc.create("Чашка", b"\xff\xd8\xff-data", "image/jpeg")
    r = await client.get("/api/products")
    body = r.json()
    assert body[0]["name"] == "Чашка"
    assert body[0]["image_url"] == f"/api/products/{p.id}/image"
    img = await client.get(body[0]["image_url"])
    assert img.status_code == 200
    assert img.content == b"\xff\xd8\xff-data"
    assert img.headers["content-type"] == "image/jpeg"


async def test_webhook_wrong_secret(client):
    r = await client.post("/bot/webhook/wrong", json={"update_id": 1})
    assert r.status_code == 404


async def test_webhook_bot_disabled(client):
    r = await client.post("/bot/webhook/s3cret", json={"update_id": 1})
    assert r.status_code == 503
