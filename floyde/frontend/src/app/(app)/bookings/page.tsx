"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Booking } from "@/lib/types";
import { Badge, Button, Card } from "@/components/ui";
import { clsx } from "@/lib/clsx";

const STATUS_STYLES: Record<string, string> = {
  confirmed: "text-green-700 bg-green-50 dark:text-green-400 dark:bg-green-950/40",
  pending: "text-amber-700 bg-amber-50 dark:text-amber-400 dark:bg-amber-950/40",
  completed: "text-zinc-600 bg-zinc-100 dark:text-zinc-300 dark:bg-zinc-900",
  cancelled: "text-red-700 bg-red-50 dark:text-red-400 dark:bg-red-950/40",
  no_show: "text-red-700 bg-red-50 dark:text-red-400 dark:bg-red-950/40",
};

function formatWhen(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "long",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function BookingsPage() {
  const [bookings, setBookings] = useState<Booking[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api
      .myBookings()
      .then(setBookings)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"));
  }, []);

  useEffect(load, [load]);

  async function cancel(id: number) {
    try {
      await api.cancelBooking(id);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Cancel failed");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Your bookings</h1>
        <Link href="/flex">
          <Button>New cut</Button>
        </Link>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {bookings && bookings.length === 0 && (
        <Card>
          <p className="text-sm text-zinc-500">
            No bookings yet.{" "}
            <Link href="/flex" className="font-medium underline-offset-2 hover:underline">
              Book a Flex Cut
            </Link>
            .
          </p>
        </Card>
      )}

      <div className="space-y-3">
        {bookings?.map((b) => {
          const active = b.status === "confirmed" || b.status === "pending";
          return (
            <Card key={b.id}>
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{formatWhen(b.start_time)}</span>
                    <span
                      className={clsx(
                        "rounded-md px-2 py-0.5 text-xs font-medium capitalize",
                        STATUS_STYLES[b.status] ?? STATUS_STYLES.completed,
                      )}
                    >
                      {b.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-zinc-500">
                    {b.source === "flex" ? "Flex cut" : b.source} · deposit $
                    {(b.deposit_cents / 100).toFixed(2)}
                    {b.match_score != null && (
                      <>
                        {" · "}
                        <Badge>{Math.round(b.match_score * 100)} fit</Badge>
                      </>
                    )}
                  </p>
                </div>
                {active && (
                  <Button variant="danger" onClick={() => cancel(b.id)}>
                    Cancel
                  </Button>
                )}
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
