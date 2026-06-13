"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useShop } from "@/lib/shop";
import type { AmazonRec, Product } from "@/lib/types";
import { dollars } from "@/lib/format";
import { Button, Card, Input, Label } from "@/components/ui";
import { clsx } from "@/lib/clsx";

export default function InventoryPage() {
  const { shopId } = useShop();
  const [products, setProducts] = useState<Product[]>([]);
  const [recs, setRecs] = useState<AmazonRec[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const load = useCallback(() => {
    if (!shopId) return;
    setError(null);
    api
      .products(shopId)
      .then(setProducts)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"));
    api
      .reorderSuggestions(shopId)
      .then(setRecs)
      .catch(() => setRecs([]));
  }, [shopId]);

  useEffect(load, [load]);

  if (!shopId) return <p className="text-sm text-zinc-400">Select a shop first.</p>;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Inventory</h1>
        <Button onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Close" : "Add product"}
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {showForm && (
        <AddProductForm
          shopId={shopId}
          onDone={() => {
            setShowForm(false);
            load();
          }}
        />
      )}

      <Card className="p-0">
        {products.length === 0 && (
          <p className="p-5 text-sm text-zinc-500">No products tracked yet.</p>
        )}
        <ul className="divide-y divide-zinc-100 dark:divide-zinc-900">
          {products.map((p) => {
            const low = p.quantity <= p.reorder_threshold;
            return (
              <li key={p.id} className="flex items-center justify-between px-5 py-3">
                <div>
                  <span className="font-medium">{p.name}</span>
                  {p.brand && (
                    <span className="ml-2 text-sm text-zinc-400">{p.brand}</span>
                  )}
                  {p.price_cents > 0 && (
                    <span className="ml-2 text-sm text-zinc-500">
                      {dollars(p.price_cents)}
                    </span>
                  )}
                </div>
                <span
                  className={clsx(
                    "rounded-md px-2 py-0.5 text-xs font-medium tabular-nums",
                    low
                      ? "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400"
                      : "bg-zinc-100 text-zinc-500 dark:bg-zinc-900",
                  )}
                >
                  {p.quantity} in stock{low ? " · low" : ""}
                </span>
              </li>
            );
          })}
        </ul>
      </Card>

      <div>
        <h2 className="mb-1 text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Restock suggestions
        </h2>
        <p className="mb-3 text-sm text-zinc-500">
          Amazon picks for everything below its reorder threshold.
        </p>
        {recs.length === 0 ? (
          <Card>
            <p className="text-sm text-zinc-500">
              Nothing to reorder — stock looks healthy.
            </p>
          </Card>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {recs.map((r) => (
              <Card key={r.asin}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{r.title}</p>
                    <p className="mt-0.5 text-sm text-zinc-500">
                      {r.brand} · {r.price}
                      {r.rating != null && ` · ${r.rating}★`}
                    </p>
                  </div>
                  <a href={r.url} target="_blank" rel="noopener noreferrer">
                    <Button variant="ghost">View</Button>
                  </a>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AddProductForm({
  shopId,
  onDone,
}: {
  shopId: number;
  onDone: () => void;
}) {
  const [name, setName] = useState("");
  const [brand, setBrand] = useState("");
  const [quantity, setQuantity] = useState("0");
  const [threshold, setThreshold] = useState("3");
  const [price, setPrice] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.addProduct({
        shop_id: shopId,
        name,
        brand,
        quantity: Number(quantity) || 0,
        reorder_threshold: Number(threshold) || 0,
        price_cents: price ? Math.round(parseFloat(price) * 100) : 0,
      });
      onDone();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to add");
      setBusy(false);
    }
  }

  return (
    <Card>
      <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label>Name</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div>
          <Label>Brand</Label>
          <Input value={brand} onChange={(e) => setBrand(e.target.value)} />
        </div>
        <div>
          <Label>Quantity</Label>
          <Input
            type="number"
            min="0"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
          />
        </div>
        <div>
          <Label>Reorder threshold</Label>
          <Input
            type="number"
            min="0"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
          />
        </div>
        <div>
          <Label>Retail price (USD, optional)</Label>
          <Input
            type="number"
            step="0.01"
            min="0"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            placeholder="16.00"
          />
        </div>
        {error && <p className="text-sm text-red-600 sm:col-span-2">{error}</p>}
        <div className="sm:col-span-2">
          <Button type="submit" disabled={busy}>
            {busy ? "Adding…" : "Add product"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
