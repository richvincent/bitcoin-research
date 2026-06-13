"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useShop } from "@/lib/shop";
import type { ProviderDetail } from "@/lib/types";
import { dollars } from "@/lib/format";
import { Badge, Button, Card, Input, Label } from "@/components/ui";
import { Stars } from "@/components/Stars";

export default function ProviderPage() {
  const params = useParams<{ id: string }>();
  const providerId = Number(params.id);
  const { user } = useAuth();
  const { shopId } = useShop();

  const [provider, setProvider] = useState<ProviderDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cart, setCart] = useState<Record<number, number>>({});
  const [placedOrderId, setPlacedOrderId] = useState<number | null>(null);
  const [orderError, setOrderError] = useState<string | null>(null);
  const [placing, setPlacing] = useState(false);

  const load = useCallback(() => {
    setError(null);
    api
      .provider(providerId)
      .then(setProvider)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Not found"));
  }, [providerId]);

  useEffect(load, [load]);

  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!provider) return <p className="text-sm text-zinc-400">Loading…</p>;

  const isOwner = !!user && provider.created_by === user.id;

  function setQty(id: number, qty: number) {
    setPlacedOrderId(null);
    setCart((c) => {
      const next = { ...c };
      if (qty <= 0) delete next[id];
      else next[id] = qty;
      return next;
    });
  }

  const cartLines = Object.entries(cart)
    .map(([id, qty]) => ({
      offering: provider!.offerings.find((o) => o.id === Number(id)),
      qty,
    }))
    .filter((l) => l.offering);
  const cartTotal = cartLines.reduce(
    (sum, l) => sum + (l.offering!.price_cents ?? 0) * l.qty,
    0,
  );

  async function placeOrder() {
    setPlacing(true);
    setOrderError(null);
    try {
      const order = await api.createOrder({
        provider_id: providerId,
        items: cartLines.map((l) => ({
          offering_id: l.offering!.id,
          quantity: l.qty,
        })),
        buyer_shop_id: shopId,
      });
      setCart({});
      setPlacedOrderId(order.id);
    } catch (e) {
      setOrderError(e instanceof ApiError ? e.message : "Checkout failed");
    } finally {
      setPlacing(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-8">
      <Link
        href="/dashboard/marketplace"
        className="text-sm text-zinc-500 hover:underline"
      >
        ← Marketplace
      </Link>

      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{provider.name}</h1>
          <div className="mt-2 flex items-center gap-2">
            <Badge>{provider.category}</Badge>
            {provider.location && (
              <span className="text-sm text-zinc-400">{provider.location}</span>
            )}
          </div>
          {provider.description && (
            <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-300">
              {provider.description}
            </p>
          )}
          {provider.website && (
            <a
              href={provider.website}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-block text-sm text-zinc-900 underline-offset-2 hover:underline dark:text-zinc-100"
            >
              Visit website ↗
            </a>
          )}
        </div>
        <div className="text-right">
          <Stars value={provider.rating} size="lg" />
          <div className="mt-1 text-xs text-zinc-400">
            {provider.review_count
              ? `${provider.rating.toFixed(1)} · ${provider.review_count} review${
                  provider.review_count > 1 ? "s" : ""
                }`
              : "No reviews yet"}
          </div>
        </div>
      </header>

      <section>
        <h2 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Offerings
        </h2>
        <div className="space-y-2">
          {provider.offerings.length === 0 && (
            <Card>
              <p className="text-sm text-zinc-500">No offerings listed.</p>
            </Card>
          )}
          {provider.offerings.map((o) => (
            <Card key={o.id}>
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="font-medium">{o.title}</p>
                  {o.description && (
                    <p className="text-sm text-zinc-500">{o.description}</p>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  <span className="whitespace-nowrap text-sm font-medium tabular-nums">
                    {o.price_cents != null
                      ? `${dollars(o.price_cents)}${o.unit ? ` ${o.unit}` : ""}`
                      : "Contact for pricing"}
                  </span>
                  {!isOwner && o.price_cents != null && (
                    <QtyControl
                      qty={cart[o.id] ?? 0}
                      onChange={(q) => setQty(o.id, q)}
                    />
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>

        {cartLines.length > 0 && (
          <Card className="mt-3 border-zinc-300 dark:border-zinc-700">
            <p className="mb-2 text-sm font-medium">Your order</p>
            <ul className="mb-3 space-y-1 text-sm">
              {cartLines.map((l) => (
                <li key={l.offering!.id} className="flex justify-between">
                  <span className="text-zinc-600 dark:text-zinc-300">
                    {l.offering!.title} × {l.qty}
                  </span>
                  <span className="tabular-nums">
                    {dollars((l.offering!.price_cents ?? 0) * l.qty)}
                  </span>
                </li>
              ))}
            </ul>
            <div className="flex items-center justify-between border-t border-zinc-100 pt-2 text-sm font-medium dark:border-zinc-900">
              <span>Total</span>
              <span className="tabular-nums">{dollars(cartTotal)}</span>
            </div>
            {orderError && <p className="mt-2 text-sm text-red-600">{orderError}</p>}
            <Button
              className="mt-3 w-full"
              onClick={placeOrder}
              disabled={placing}
            >
              {placing ? "Placing order…" : `Place order · ${dollars(cartTotal)}`}
            </Button>
          </Card>
        )}

        {placedOrderId && (
          <Card className="mt-3 border-green-200 bg-green-50/60 dark:border-green-900/50 dark:bg-green-950/20">
            <p className="text-sm text-green-800 dark:text-green-300">
              Order #{placedOrderId} placed and paid.{" "}
              <Link
                href="/dashboard/marketplace/orders"
                className="font-medium underline-offset-2 hover:underline"
              >
                View your orders →
              </Link>
            </p>
          </Card>
        )}

        {isOwner && <AddOffering providerId={providerId} onDone={load} />}
      </section>

      <section>
        <h2 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Reviews
        </h2>
        {!isOwner && user && (
          <ReviewForm providerId={providerId} onDone={load} />
        )}
        <div className="mt-4 space-y-3">
          {provider.reviews.length === 0 && (
            <p className="text-sm text-zinc-500">Be the first to review.</p>
          )}
          {provider.reviews.map((r) => (
            <Card key={r.id}>
              <div className="flex items-center justify-between">
                <span className="font-medium">{r.author_name}</span>
                <Stars value={r.rating} />
              </div>
              {r.title && <p className="mt-2 font-medium">{r.title}</p>}
              {r.body && (
                <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">
                  {r.body}
                </p>
              )}
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}

function QtyControl({
  qty,
  onChange,
}: {
  qty: number;
  onChange: (q: number) => void;
}) {
  if (qty === 0) {
    return (
      <Button variant="ghost" onClick={() => onChange(1)}>
        Add
      </Button>
    );
  }
  return (
    <div className="flex items-center gap-1">
      <button
        onClick={() => onChange(qty - 1)}
        className="h-7 w-7 rounded-md border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
        aria-label="Decrease"
      >
        −
      </button>
      <span className="w-6 text-center text-sm tabular-nums">{qty}</span>
      <button
        onClick={() => onChange(qty + 1)}
        className="h-7 w-7 rounded-md border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
        aria-label="Increase"
      >
        +
      </button>
    </div>
  );
}

function ReviewForm({
  providerId,
  onDone,
}: {
  providerId: number;
  onDone: () => void;
}) {
  const [rating, setRating] = useState(5);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.addReview(providerId, { rating, title, body });
      setTitle("");
      setBody("");
      onDone();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not submit review");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <form onSubmit={submit} className="space-y-3">
        <div className="flex items-center gap-3">
          <Label>Your rating</Label>
          <Stars value={rating} onChange={setRating} />
        </div>
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Headline (optional)"
        />
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={2}
          placeholder="How was your experience?"
          className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm placeholder:text-zinc-400 focus:border-zinc-400 focus:outline-none dark:border-zinc-800 dark:bg-zinc-950"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={busy}>
          {busy ? "Submitting…" : "Submit review"}
        </Button>
      </form>
    </Card>
  );
}

function AddOffering({
  providerId,
  onDone,
}: {
  providerId: number;
  onDone: () => void;
}) {
  const [title, setTitle] = useState("");
  const [price, setPrice] = useState("");
  const [unit, setUnit] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.addOffering(providerId, {
        title,
        price_cents: price ? Math.round(parseFloat(price) * 100) : null,
        unit,
      });
      setTitle("");
      setPrice("");
      setUnit("");
      onDone();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not add offering");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="mt-2">
      <form onSubmit={submit} className="grid items-end gap-3 sm:grid-cols-4">
        <div className="sm:col-span-2">
          <Label>New offering</Label>
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Liability plan"
            required
          />
        </div>
        <div>
          <Label>Price (USD)</Label>
          <Input
            type="number"
            step="0.01"
            min="0"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            placeholder="optional"
          />
        </div>
        <div>
          <Label>Unit</Label>
          <Input
            value={unit}
            onChange={(e) => setUnit(e.target.value)}
            placeholder="per month"
          />
        </div>
        {error && <p className="text-sm text-red-600 sm:col-span-4">{error}</p>}
        <div className="sm:col-span-4">
          <Button type="submit" disabled={busy}>
            {busy ? "Adding…" : "Add offering"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
