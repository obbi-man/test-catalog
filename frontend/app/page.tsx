// Серверный компонент: данные берутся на каждый запрос, состояния на фронтенде нет.
export const dynamic = "force-dynamic";

type Product = { id: number; name: string; image_url: string };

async function getProducts(): Promise<Product[]> {
  const base = process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000";
  const res = await fetch(`${base}/api/products`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
  return res.json();
}

export default async function CatalogPage() {
  const products = await getProducts();
  return (
    <main>
      <h1>Каталог</h1>
      {products.length === 0 && <p>Пока нет товаров</p>}
      <ul>
        {products.map((p) => (
          <li key={p.id}>
            <div>{p.name}</div>
            {/* Картинка отдаётся через nginx -> backend (/api/products/{id}/image) -> MinIO */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={p.image_url} alt={p.name} width={200} />
          </li>
        ))}
      </ul>
    </main>
  );
}
