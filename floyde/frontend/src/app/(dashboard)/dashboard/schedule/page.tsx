"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useShop } from "@/lib/shop";
import type { Barber, ManagedBooking, Service } from "@/lib/types";
import { dollars, formatDateTime } from "@/lib/format";
import { Badge, Button, Card, Input, Label } from "@/components/ui";
import { StatusPill } from "@/components/StatusPill";

export default function SchedulePage() {
  const { shopId } = useShop();
  const [rows, setRows] = useState<ManagedBooking[]>([]);
  const [barbers, setBarbers] = useState<Barber[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const load = useCallback(() => {
    if (!shopId) return;
    setError(null);
    Promise.all([
      api.manageSchedule(shopId),
      api.barbers(shopId),
      api.services(shopId),
    ])
      .then(([b, br, sv]) => {
        setRows(b);
        setBarbers(br);
        setServices(sv);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"));
  }, [shopId]);

  useEffect(load, [load]);

  async function act(id: number, fn: (id: number) => Promise<unknown>) {
    try {
      await fn(id);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Action failed");
    }
  }

  if (!shopId) return <p className="text-sm text-zinc-400">Select a shop first.</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Schedule</h1>
        <Button onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Close" : "Add walk-in"}
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {showForm && (
        <WalkInForm
          shopId={shopId}
          barbers={barbers}
          services={services}
          onDone={() => {
            setShowForm(false);
            load();
          }}
        />
      )}

      <div className="space-y-2">
        {rows.length === 0 && (
          <Card>
            <p className="text-sm text-zinc-500">No bookings yet.</p>
          </Card>
        )}
        {rows.map((b) => {
          const active = b.status === "confirmed" || b.status === "pending";
          return (
            <Card key={b.id}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{formatDateTime(b.start_time)}</span>
                    <StatusPill status={b.status} />
                    {b.source === "walk_in" && <Badge>walk-in</Badge>}
                  </div>
                  <p className="mt-1 text-sm text-zinc-500">
                    {b.client_name} · {b.service_name} · {b.barber_name} ·{" "}
                    {dollars(b.price_cents)}
                  </p>
                </div>
                {active && (
                  <div className="flex gap-2">
                    {b.status === "pending" && (
                      <Button
                        variant="ghost"
                        onClick={() => act(b.id, api.confirmBooking)}
                      >
                        Confirm
                      </Button>
                    )}
                    <Button variant="ghost" onClick={() => act(b.id, api.completeBooking)}>
                      Complete
                    </Button>
                    <Button variant="danger" onClick={() => act(b.id, api.cancelBooking)}>
                      Cancel
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

function WalkInForm({
  shopId,
  barbers,
  services,
  onDone,
}: {
  shopId: number;
  barbers: Barber[];
  services: Service[];
  onDone: () => void;
}) {
  const [email, setEmail] = useState("");
  const [barberId, setBarberId] = useState<number | "">(barbers[0]?.id ?? "");
  const [serviceId, setServiceId] = useState<number | "">(services[0]?.id ?? "");
  const [when, setWhen] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!barberId || !serviceId || !when) return;
    setBusy(true);
    setError(null);
    try {
      await api.staffBooking({
        client_email: email,
        barber_id: Number(barberId),
        service_id: Number(serviceId),
        start_time: new Date(when).toISOString(),
        source: "walk_in",
      });
      onDone();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Booking failed");
      setBusy(false);
    }
  }

  return (
    <Card>
      <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Label>Client email (must have an account)</Label>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="client@floyde.app"
            required
          />
        </div>
        <div>
          <Label>Barber</Label>
          <select
            value={barberId}
            onChange={(e) => setBarberId(Number(e.target.value))}
            className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-800 dark:bg-zinc-950"
            required
          >
            {barbers.map((b) => (
              <option key={b.id} value={b.id}>
                {b.display_name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <Label>Service</Label>
          <select
            value={serviceId}
            onChange={(e) => setServiceId(Number(e.target.value))}
            className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-800 dark:bg-zinc-950"
            required
          >
            {services.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
        <div className="sm:col-span-2">
          <Label>When</Label>
          <Input
            type="datetime-local"
            value={when}
            onChange={(e) => setWhen(e.target.value)}
            required
          />
        </div>
        {error && <p className="text-sm text-red-600 sm:col-span-2">{error}</p>}
        <div className="sm:col-span-2">
          <Button type="submit" disabled={busy}>
            {busy ? "Booking…" : "Book walk-in"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
