"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Order } from "@/lib/types";
import { dollars, formatDateTime } from "@/lib/format";
import { Button, Card } from "@/components/ui";
import { clsx } from "@/lib/clsx";

const STATUS_STYLES: Record<string, string> = {
  paid: "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400",
  pending: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400",
  fulfilled: "bg-green-50 text-green-700 dark:bg-green-950/40 dark:text-green-400",
  cancelled: "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-400",
  refunded: "bg-zinc-100 text-zinc-500 dark:bg-zinc-900 dark:text-zinc-400",
};

type Tab = "buyer" | "seller";

export default function OrdersPage() {
  const [tab, setTab] = useState<Tab>("buyer");
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    api
      .orders(tab)
      .then(setOrders)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"));
  }, [tab]);

  useEffect(load, [load]);

  async function act(id: number, fn: (id: number) => Promise<unknown>) {
    try {
      await fn(id);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Action failed");
    }
  }

  // Seller earnings (payout net of platform commission) on fulfilled/paid orders.
  const earnings = orders
    .filter((o) => o.status === "paid" || o.status === "fulfilled")
    .reduce((s, o) => s + o.provider_payout_cents, 0);
  const spend = orders
    .filter((o) => o.status !== "cancelled")
    .reduce((s, o) => s + o.subtotal_cents, 0);

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Orders</h1>
        <Link href="/dashboard/marketplace" className="text-sm text-zinc-500 hover:underline">
          ← Marketplace
        </Link>
      </div>

      <div className="flex items-center gap-2">
        <TabButton active={tab === "buyer"} onClick={() => setTab("buyer")}>
          Purchases
        </TabButton>
        <TabButton active={tab === "seller"} onClick={() => setTab("seller")}>
          Sales
        </TabButton>
      </div>

      {orders.length > 0 && (
        <Card>
          <div className="flex items-center justify-between text-sm">
            <span className="text-zinc-500">
              {tab === "buyer" ? "Total spend" : "Net earnings (after platform fee)"}
            </span>
            <span className="text-lg font-semibold tabular-nums">
              {dollars(tab === "buyer" ? spend : earnings)}
            </span>
          </div>
        </Card>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-3">
        {orders.length === 0 && (
          <Card>
            <p className="text-sm text-zinc-500">
              {tab === "buyer"
                ? "No purchases yet. Browse the marketplace to order supplies."
                : "No sales yet. List offerings on your provider page."}
            </p>
          </Card>
        )}
        {orders.map((o) => (
          <Card key={o.id}>
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium">
                    {tab === "buyer" ? o.provider_name : o.buyer_name}
                  </span>
                  <span
                    className={clsx(
                      "rounded-md px-2 py-0.5 text-xs font-medium capitalize",
                      STATUS_STYLES[o.status],
                    )}
                  >
                    {o.status}
                  </span>
                </div>
                <ul className="mt-1 text-sm text-zinc-500">
                  {o.items.map((it) => (
                    <li key={it.id}>
                      {it.title} × {it.quantity} ·{" "}
                      {dollars(it.line_total_cents)}
                    </li>
                  ))}
                </ul>
                <p className="mt-1 text-xs text-zinc-400">
                  #{o.id} · {formatDateTime(o.created_at)}
                </p>
              </div>
              <div className="flex flex-col items-end gap-2">
                <div className="text-right">
                  <div className="font-semibold tabular-nums">
                    {dollars(o.subtotal_cents)}
                  </div>
                  <div className="text-xs text-zinc-400">
                    {tab === "seller"
                      ? `net ${dollars(o.provider_payout_cents)}`
                      : `incl. ${dollars(o.commission_cents)} fee`}
                  </div>
                </div>
                {tab === "seller" && o.status === "paid" && (
                  <Button variant="ghost" onClick={() => act(o.id, api.fulfillOrder)}>
                    Mark fulfilled
                  </Button>
                )}
                {o.status !== "fulfilled" && o.status !== "cancelled" && (
                  <Button variant="danger" onClick={() => act(o.id, api.cancelOrder)}>
                    Cancel
                  </Button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
        active
          ? "bg-zinc-900 text-white dark:bg-white dark:text-zinc-900"
          : "border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900",
      )}
    >
      {children}
    </button>
  );
}
