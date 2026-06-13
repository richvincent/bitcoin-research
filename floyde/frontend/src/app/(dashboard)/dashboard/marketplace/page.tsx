"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Provider, ProviderCategory } from "@/lib/types";
import { dollarsShort } from "@/lib/format";
import { Badge, Button, Card, Input, Label } from "@/components/ui";
import { Stars } from "@/components/Stars";
import { clsx } from "@/lib/clsx";

export default function MarketplacePage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [category, setCategory] = useState<string>("");
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const load = useCallback(() => {
    setError(null);
    api
      .providers({ category: category || undefined, q: q || undefined })
      .then(setProviders)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"));
  }, [category, q]);

  useEffect(() => {
    api.marketplaceCategories().then(setCategories).catch(() => setCategories([]));
  }, []);
  useEffect(load, [load]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Marketplace</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Vetted suppliers, insurance, marketing, and more for your shop.
          </p>
        </div>
        <Button onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Close" : "List your business"}
        </Button>
      </div>

      {showForm && (
        <NewProvider
          categories={categories}
          onDone={() => {
            setShowForm(false);
            load();
          }}
        />
      )}

      <div className="flex flex-wrap items-center gap-3">
        <Input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search providers…"
          className="max-w-xs"
        />
        <div className="flex flex-wrap gap-1.5">
          <CategoryChip label="All" active={!category} onClick={() => setCategory("")} />
          {categories.map((c) => (
            <CategoryChip
              key={c}
              label={c}
              active={category === c}
              onClick={() => setCategory(c)}
            />
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="grid gap-3 sm:grid-cols-2">
        {providers.map((p) => (
          <Link key={p.id} href={`/dashboard/marketplace/${p.id}`}>
            <Card className="h-full transition-colors hover:border-zinc-300 dark:hover:border-zinc-700">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="font-medium">{p.name}</h3>
                  <div className="mt-1 flex items-center gap-2">
                    <Badge>{p.category}</Badge>
                    {p.location && (
                      <span className="text-xs text-zinc-400">{p.location}</span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <Stars value={p.rating} />
                  <div className="text-xs text-zinc-400">
                    {p.review_count
                      ? `${p.rating.toFixed(1)} · ${p.review_count}`
                      : "No reviews"}
                  </div>
                </div>
              </div>
              {p.description && (
                <p className="mt-3 line-clamp-2 text-sm text-zinc-500">
                  {p.description}
                </p>
              )}
            </Card>
          </Link>
        ))}
      </div>
      {providers.length === 0 && !error && (
        <Card>
          <p className="text-sm text-zinc-500">No providers match your filters.</p>
        </Card>
      )}
    </div>
  );
}

function CategoryChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "rounded-full border px-3 py-1 text-xs capitalize transition-colors",
        active
          ? "border-zinc-900 bg-zinc-900 text-white dark:border-white dark:bg-white dark:text-zinc-900"
          : "border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900",
      )}
    >
      {label}
    </button>
  );
}

function NewProvider({
  categories,
  onDone,
}: {
  categories: string[];
  onDone: () => void;
}) {
  const [name, setName] = useState("");
  const [category, setCategory] = useState<ProviderCategory>("supplies");
  const [description, setDescription] = useState("");
  const [website, setWebsite] = useState("");
  const [location, setLocation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.createProvider({ name, category, description, website, location });
      onDone();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to create");
      setBusy(false);
    }
  }

  return (
    <Card>
      <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label>Business name</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div>
          <Label>Category</Label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as ProviderCategory)}
            className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm capitalize dark:border-zinc-800 dark:bg-zinc-950"
          >
            {(categories.length ? categories : ["supplies"]).map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div className="sm:col-span-2">
          <Label>Description</Label>
          <Input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What you offer to barbershops"
          />
        </div>
        <div>
          <Label>Website</Label>
          <Input value={website} onChange={(e) => setWebsite(e.target.value)} />
        </div>
        <div>
          <Label>Location</Label>
          <Input value={location} onChange={(e) => setLocation(e.target.value)} />
        </div>
        {error && <p className="text-sm text-red-600 sm:col-span-2">{error}</p>}
        <div className="sm:col-span-2">
          <Button type="submit" disabled={busy}>
            {busy ? "Listing…" : "List business"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
