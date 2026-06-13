"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useShop } from "@/lib/shop";
import type { Barber, Service } from "@/lib/types";
import { dollarsShort } from "@/lib/format";
import { Badge, Button, Card, Input, Label } from "@/components/ui";

function slugify(s: string) {
  return s
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export default function SetupPage() {
  const { shop, shopId, refresh, setShopId } = useShop();
  const [services, setServices] = useState<Service[]>([]);
  const [barbers, setBarbers] = useState<Barber[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!shopId) {
      setServices([]);
      setBarbers([]);
      return;
    }
    api.services(shopId).then(setServices).catch(() => setServices([]));
    api.barbers(shopId).then(setBarbers).catch(() => setBarbers([]));
  }, [shopId]);

  useEffect(load, [load]);

  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Setup</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Configure your shop, services, and team. Owner access required.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <NewShop
        onCreated={(id) => {
          refresh();
          setShopId(id);
        }}
        onError={setError}
      />

      {shopId && (
        <>
          <section>
            <h2 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Services — {shop?.name}
            </h2>
            <div className="mb-3 flex flex-wrap gap-2">
              {services.map((s) => (
                <Badge key={s.id}>
                  {s.name} · {dollarsShort(s.price_cents)} · {s.duration_minutes}m
                </Badge>
              ))}
              {services.length === 0 && (
                <span className="text-sm text-zinc-400">No services yet.</span>
              )}
            </div>
            <NewService shopId={shopId} onDone={load} onError={setError} />
          </section>

          <section>
            <h2 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Team
            </h2>
            <div className="mb-3 flex flex-wrap gap-2">
              {barbers.map((b) => (
                <Badge key={b.id}>
                  {b.display_name} · {b.rating.toFixed(1)}★
                </Badge>
              ))}
              {barbers.length === 0 && (
                <span className="text-sm text-zinc-400">No barbers yet.</span>
              )}
            </div>
            <NewBarber shopId={shopId} onDone={load} onError={setError} />
          </section>
        </>
      )}
    </div>
  );
}

function NewShop({
  onCreated,
  onError,
}: {
  onCreated: (id: number) => void;
  onError: (msg: string) => void;
}) {
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const shop = await api.createShop({ name, slug: slugify(name), address });
      setName("");
      setAddress("");
      onCreated(shop.id);
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Failed to create shop");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <form onSubmit={submit} className="space-y-4">
        <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          New shop
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label>Name</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Mayberry Cuts"
              required
            />
          </div>
          <div>
            <Label>Address</Label>
            <Input
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="123 Main St, Detroit, MI"
            />
          </div>
        </div>
        <Button type="submit" disabled={busy}>
          {busy ? "Creating…" : "Create shop"}
        </Button>
      </form>
    </Card>
  );
}

function NewService({
  shopId,
  onDone,
  onError,
}: {
  shopId: number;
  onDone: () => void;
  onError: (msg: string) => void;
}) {
  const [name, setName] = useState("");
  const [duration, setDuration] = useState("30");
  const [price, setPrice] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.createService({
        shop_id: shopId,
        name,
        duration_minutes: Number(duration) || 30,
        price_cents: price ? Math.round(parseFloat(price) * 100) : 0,
      });
      setName("");
      setPrice("");
      onDone();
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Failed to add service");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <form onSubmit={submit} className="grid items-end gap-4 sm:grid-cols-4">
        <div className="sm:col-span-2">
          <Label>Service name</Label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Signature Haircut"
            required
          />
        </div>
        <div>
          <Label>Minutes</Label>
          <Input
            type="number"
            min="5"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
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
            placeholder="45.00"
          />
        </div>
        <div className="sm:col-span-4">
          <Button type="submit" disabled={busy}>
            {busy ? "Adding…" : "Add service"}
          </Button>
        </div>
      </form>
    </Card>
  );
}

function NewBarber({
  shopId,
  onDone,
  onError,
}: {
  shopId: number;
  onDone: () => void;
  onError: (msg: string) => void;
}) {
  const [userId, setUserId] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.addBarber({
        user_id: Number(userId),
        shop_id: shopId,
        display_name: displayName,
      });
      setUserId("");
      setDisplayName("");
      onDone();
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Failed to add barber");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <form onSubmit={submit} className="grid items-end gap-4 sm:grid-cols-3">
        <div>
          <Label>Barber user ID</Label>
          <Input
            type="number"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="e.g. 3"
            required
          />
        </div>
        <div>
          <Label>Display name</Label>
          <Input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Floyd Jr."
            required
          />
        </div>
        <div>
          <Button type="submit" disabled={busy}>
            {busy ? "Adding…" : "Add barber"}
          </Button>
        </div>
        <p className="text-xs text-zinc-400 sm:col-span-3">
          The barber must already have a Floyde account (sign up with role
          &ldquo;barber&rdquo;). Their user ID comes from that account.
        </p>
      </form>
    </Card>
  );
}
