"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ProviderDetail } from "@/lib/types";
import { dollars } from "@/lib/format";
import { Badge, Button, Card, Input, Label } from "@/components/ui";
import { Stars } from "@/components/Stars";

export default function ProviderPage() {
  const params = useParams<{ id: string }>();
  const providerId = Number(params.id);
  const { user } = useAuth();

  const [provider, setProvider] = useState<ProviderDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

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
                <div>
                  <p className="font-medium">{o.title}</p>
                  {o.description && (
                    <p className="text-sm text-zinc-500">{o.description}</p>
                  )}
                </div>
                <span className="whitespace-nowrap text-sm font-medium tabular-nums">
                  {o.price_cents != null
                    ? `${dollars(o.price_cents)}${o.unit ? ` ${o.unit}` : ""}`
                    : "Contact for pricing"}
                </span>
              </div>
            </Card>
          ))}
        </div>
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
