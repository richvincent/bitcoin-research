"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useShop } from "@/lib/shop";
import type { ShopReport } from "@/lib/types";
import { dollars } from "@/lib/format";
import { Card } from "@/components/ui";
import { clsx } from "@/lib/clsx";

const RANGES = [
  { days: 7, label: "7d" },
  { days: 30, label: "30d" },
  { days: 90, label: "90d" },
];

const TYPE_LABEL: Record<string, string> = {
  deposit: "Deposits",
  final: "Service",
  product: "Product",
};

export default function ReportsPage() {
  const { shopId, shop } = useShop();
  const [days, setDays] = useState(30);
  const [report, setReport] = useState<ShopReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!shopId) return;
    setError(null);
    api
      .report(shopId, days)
      .then(setReport)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"));
  }, [shopId, days]);

  useEffect(load, [load]);

  if (!shopId) return <p className="text-sm text-zinc-400">Select a shop first.</p>;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Reports</h1>
          <p className="mt-1 text-sm text-zinc-500">
            {shop?.name} · trailing {days} days
          </p>
        </div>
        <div className="flex gap-1">
          {RANGES.map((r) => (
            <button
              key={r.days}
              onClick={() => setDays(r.days)}
              className={clsx(
                "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                days === r.days
                  ? "bg-zinc-900 text-white dark:bg-white dark:text-zinc-900"
                  : "border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900",
              )}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {!report ? (
        <p className="text-sm text-zinc-400">Loading…</p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Stat label="Revenue" value={dollars(report.revenue_cents)} />
            <Stat label="Supply spend" value={dollars(report.supply_spend_cents)} />
            <Stat label="Net" value={dollars(report.net_cents)} />
            <Stat
              label="Completed cuts"
              value={String(report.bookings_completed)}
            />
          </div>

          <RevenueChart data={report.revenue_by_day} />

          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <h2 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Bookings
              </h2>
              <Card>
                <dl className="space-y-2 text-sm">
                  <Row label="Total in range" value={report.bookings_total} />
                  <Row label="Completed" value={report.bookings_completed} />
                  <Row label="Upcoming" value={report.bookings_upcoming} />
                  <Row label="Cancelled" value={report.bookings_cancelled} />
                  <Row label="No-show" value={report.bookings_no_show} />
                  <Row
                    label="No-show rate"
                    value={`${Math.round(report.no_show_rate * 100)}%`}
                  />
                </dl>
              </Card>

              <h2 className="mb-3 mt-6 text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Revenue by type
              </h2>
              <Card>
                {Object.keys(report.revenue_by_type).length === 0 ? (
                  <p className="text-sm text-zinc-500">No revenue yet.</p>
                ) : (
                  <dl className="space-y-2 text-sm">
                    {Object.entries(report.revenue_by_type).map(([t, cents]) => (
                      <Row
                        key={t}
                        label={TYPE_LABEL[t] ?? t}
                        value={dollars(cents)}
                      />
                    ))}
                  </dl>
                )}
              </Card>
            </div>

            <div>
              <h2 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Barber leaderboard
              </h2>
              <Card className="p-0">
                {report.barber_leaderboard.length === 0 ? (
                  <p className="p-5 text-sm text-zinc-500">
                    No completed cuts in this window.
                  </p>
                ) : (
                  <ul className="divide-y divide-zinc-100 dark:divide-zinc-900">
                    {report.barber_leaderboard.map((b, i) => (
                      <li
                        key={b.barber_id}
                        className="flex items-center justify-between px-5 py-3"
                      >
                        <span className="flex items-center gap-3">
                          <span className="w-5 text-sm text-zinc-400 tabular-nums">
                            {i + 1}
                          </span>
                          <span className="font-medium">{b.name}</span>
                        </span>
                        <span className="text-sm tabular-nums text-zinc-500">
                          {b.completed} cut{b.completed === 1 ? "" : "s"}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            </div>
          </div>
        </>
      )}
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

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between">
      <dt className="text-zinc-500">{label}</dt>
      <dd className="font-medium tabular-nums">{value}</dd>
    </div>
  );
}

function RevenueChart({ data }: { data: { date: string; cents: number }[] }) {
  const max = Math.max(1, ...data.map((d) => d.cents));
  // Keep the bar count readable for long ranges.
  const step = Math.ceil(data.length / 30);
  const points = data.filter((_, i) => i % step === 0);

  return (
    <div>
      <h2 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
        Daily revenue
      </h2>
      <Card>
        {data.every((d) => d.cents === 0) ? (
          <p className="text-sm text-zinc-500">No revenue in this window yet.</p>
        ) : (
          <div className="flex h-32 items-end gap-1">
            {points.map((d) => (
              <div
                key={d.date}
                className="group relative flex-1"
                title={`${d.date}: ${dollars(d.cents)}`}
              >
                <div
                  className="w-full rounded-t bg-zinc-300 transition-colors group-hover:bg-zinc-900 dark:bg-zinc-700 dark:group-hover:bg-white"
                  style={{ height: `${Math.max(2, (d.cents / max) * 100)}%` }}
                />
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
