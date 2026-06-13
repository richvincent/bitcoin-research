"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useShop } from "@/lib/shop";
import type { Payment } from "@/lib/types";
import { dollars } from "@/lib/format";
import { Button, Card, Input, Label } from "@/components/ui";
import { clsx } from "@/lib/clsx";

const TYPES = [
  { value: "final", label: "Service" },
  { value: "product", label: "Product" },
  { value: "deposit", label: "Deposit" },
];

export default function PosPage() {
  const { shopId } = useShop();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [amount, setAmount] = useState("");
  const [type, setType] = useState("final");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!shopId) return;
    api
      .payments(shopId)
      .then(setPayments)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"));
  }, [shopId]);

  useEffect(load, [load]);

  async function charge(e: React.FormEvent) {
    e.preventDefault();
    if (!shopId) return;
    const cents = Math.round(parseFloat(amount) * 100);
    if (!cents || cents <= 0) {
      setError("Enter a valid amount");
      return;
    }
    setBusy(true);
    setError(null);
    setNote(null);
    try {
      const res = await api.charge({
        shop_id: shopId,
        amount_cents: cents,
        type,
      });
      setNote(
        res.payment.status === "succeeded"
          ? `Charged ${dollars(res.payment.amount_cents)} (stub mode — auto-approved).`
          : `Payment intent created (${res.payment.status}).`,
      );
      setAmount("");
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Charge failed");
    } finally {
      setBusy(false);
    }
  }

  if (!shopId) return <p className="text-sm text-zinc-400">Select a shop first.</p>;

  const total = payments
    .filter((p) => p.status === "succeeded")
    .reduce((s, p) => s + p.amount_cents, 0);

  return (
    <div className="grid gap-8 lg:grid-cols-[360px_1fr]">
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold tracking-tight">Point of sale</h1>
        <Card>
          <form onSubmit={charge} className="space-y-4">
            <div>
              <Label>Amount (USD)</Label>
              <Input
                type="number"
                inputMode="decimal"
                step="0.01"
                min="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="45.00"
                required
              />
            </div>
            <div>
              <Label>Type</Label>
              <div className="flex gap-2">
                {TYPES.map((t) => (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => setType(t.value)}
                    className={clsx(
                      "flex-1 rounded-lg border px-3 py-2 text-sm transition-colors",
                      type === t.value
                        ? "border-zinc-900 bg-zinc-900 text-white dark:border-white dark:bg-white dark:text-zinc-900"
                        : "border-zinc-200 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900",
                    )}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
            <Button type="submit" className="w-full" disabled={busy}>
              {busy ? "Processing…" : "Charge"}
            </Button>
            {note && (
              <p className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700 dark:bg-green-950/40 dark:text-green-400">
                {note}
              </p>
            )}
            {error && <p className="text-sm text-red-600">{error}</p>}
          </form>
        </Card>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Recent payments
          </h2>
          <span className="text-sm text-zinc-500">
            {dollars(total)} collected
          </span>
        </div>
        <Card className="p-0">
          {payments.length === 0 && (
            <p className="p-5 text-sm text-zinc-500">No payments yet.</p>
          )}
          <ul className="divide-y divide-zinc-100 dark:divide-zinc-900">
            {payments.map((p) => (
              <li key={p.id} className="flex items-center justify-between px-5 py-3">
                <div>
                  <span className="font-medium tabular-nums">
                    {dollars(p.amount_cents)}
                  </span>
                  <span className="ml-2 text-sm capitalize text-zinc-500">
                    {p.type}
                    {p.booking_id ? ` · booking #${p.booking_id}` : ""}
                  </span>
                </div>
                <span
                  className={clsx(
                    "rounded-md px-2 py-0.5 text-xs font-medium capitalize",
                    p.status === "succeeded"
                      ? "bg-green-50 text-green-700 dark:bg-green-950/40 dark:text-green-400"
                      : "bg-zinc-100 text-zinc-500 dark:bg-zinc-900",
                  )}
                >
                  {p.status}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
