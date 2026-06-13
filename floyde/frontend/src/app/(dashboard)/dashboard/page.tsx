"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { useShop } from "@/lib/shop";
import type { ManagedBooking, Payment, Product } from "@/lib/types";
import { dollars, formatTime, isToday } from "@/lib/format";
import { Badge, Button, Card } from "@/components/ui";
import { StatusPill } from "@/components/StatusPill";

export default function OverviewPage() {
  const { shopId, shop, loading: shopLoading } = useShop();
  const [bookings, setBookings] = useState<ManagedBooking[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!shopId) return;
    setError(null);
    Promise.all([
      api.manageSchedule(shopId),
      api.payments(shopId),
      api.products(shopId),
    ])
      .then(([b, p, pr]) => {
        setBookings(b);
        setPayments(p);
        setProducts(pr);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"));
  }, [shopId]);

  useEffect(load, [load]);

  async function complete(id: number) {
    await api.completeBooking(id);
    load();
  }

  if (shopLoading) return <p className="text-sm text-zinc-400">Loading…</p>;
  if (!shopId)
    return (
      <Card>
        <p className="text-sm text-zinc-500">
          No shop yet.{" "}
          <Link href="/dashboard/setup" className="font-medium underline-offset-2 hover:underline">
            Create one in Setup
          </Link>
          .
        </p>
      </Card>
    );

  const todays = bookings
    .filter((b) => isToday(b.start_time))
    .sort((a, b) => a.start_time.localeCompare(b.start_time));
  const upcoming = todays.filter(
    (b) => b.status === "confirmed" || b.status === "pending",
  );
  const completedToday = todays.filter((b) => b.status === "completed").length;
  const revenueToday = payments
    .filter((p) => p.status === "succeeded")
    .reduce((sum, p) => sum + p.amount_cents, 0);
  const lowStock = products.filter((p) => p.quantity <= p.reorder_threshold);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{shop?.name}</h1>
        <p className="mt-1 text-sm text-zinc-500">Today at a glance.</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Today's appts" value={String(todays.length)} />
        <Stat label="Upcoming" value={String(upcoming.length)} />
        <Stat label="Completed" value={String(completedToday)} />
        <Stat label="Revenue (paid)" value={dollars(revenueToday)} />
      </div>

      {lowStock.length > 0 && (
        <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20">
          <div className="flex items-center justify-between">
            <p className="text-sm text-amber-800 dark:text-amber-300">
              {lowStock.length} item{lowStock.length > 1 ? "s" : ""} low on stock:{" "}
              {lowStock.map((p) => p.name).join(", ")}
            </p>
            <Link href="/dashboard/inventory">
              <Button variant="ghost">Reorder</Button>
            </Link>
          </div>
        </Card>
      )}

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Today&apos;s schedule
          </h2>
          <Link href="/dashboard/schedule" className="text-sm text-zinc-500 hover:underline">
            View all →
          </Link>
        </div>
        <div className="space-y-2">
          {todays.length === 0 && (
            <Card>
              <p className="text-sm text-zinc-500">Nothing booked for today yet.</p>
            </Card>
          )}
          {todays.map((b) => (
            <Card key={b.id}>
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <span className="w-16 text-sm font-medium tabular-nums">
                    {formatTime(b.start_time)}
                  </span>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{b.client_name}</span>
                      <StatusPill status={b.status} />
                    </div>
                    <p className="text-sm text-zinc-500">
                      {b.service_name} · {b.barber_name}
                      {b.source === "walk_in" && (
                        <>
                          {" "}
                          <Badge>walk-in</Badge>
                        </>
                      )}
                    </p>
                  </div>
                </div>
                {(b.status === "confirmed" || b.status === "pending") && (
                  <Button variant="ghost" onClick={() => complete(b.id)}>
                    Complete
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <div className="text-2xl font-semibold tabular-nums">{value}</div>
      <div className="mt-1 text-xs text-zinc-500">{label}</div>
    </Card>
  );
}
