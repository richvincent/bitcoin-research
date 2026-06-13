"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useShop } from "@/lib/shop";
import type { ConciergeRequest, ConciergeStatus } from "@/lib/types";
import { formatDateTime } from "@/lib/format";
import { Button, Card } from "@/components/ui";
import { clsx } from "@/lib/clsx";

const STATUS_STYLES: Record<string, string> = {
  queued: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400",
  in_progress: "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400",
  completed: "bg-zinc-100 text-zinc-500 dark:bg-zinc-900 dark:text-zinc-400",
  cancelled: "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-400",
};

export default function ConciergePage() {
  const { shopId } = useShop();
  const [requests, setRequests] = useState<ConciergeRequest[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    api
      .conciergeRequests(shopId ?? undefined)
      .then(setRequests)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"));
  }, [shopId]);

  useEffect(load, [load]);

  async function setStatus(id: number, status: ConciergeStatus) {
    try {
      await api.updateConciergeStatus(id, status);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Update failed");
    }
  }

  async function call(id: number) {
    try {
      await api.callConcierge(id);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not place the call");
    }
  }

  const open = requests.filter(
    (r) => r.status === "queued" || r.status === "in_progress",
  );

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          <span className="text-amber-500">✦</span> Concierge desk
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          Premium live-voice (Ruby) callback requests. {open.length} open.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-2">
        {requests.length === 0 && (
          <Card>
            <p className="text-sm text-zinc-500">No concierge requests yet.</p>
          </Card>
        )}
        {requests.map((r) => {
          const active = r.status === "queued" || r.status === "in_progress";
          return (
            <Card key={r.id}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{r.client_name || "Client"}</span>
                    <span
                      className={clsx(
                        "rounded-md px-2 py-0.5 text-xs font-medium capitalize",
                        STATUS_STYLES[r.status],
                      )}
                    >
                      {r.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">
                    {r.topic}
                  </p>
                  <p className="mt-0.5 text-xs text-zinc-400">
                    {r.phone} · {formatDateTime(r.created_at)} · {r.request_id}
                  </p>
                  {r.call_sid && (
                    <p className="mt-1 text-xs text-blue-600 dark:text-blue-400">
                      ☎ Call placed · {r.call_sid}
                    </p>
                  )}
                </div>
                {active && (
                  <div className="flex flex-wrap justify-end gap-2">
                    {r.status === "queued" && (
                      <Button onClick={() => call(r.id)}>Call now</Button>
                    )}
                    {r.status === "in_progress" && (
                      <Button variant="ghost" onClick={() => call(r.id)}>
                        Redial
                      </Button>
                    )}
                    <Button variant="ghost" onClick={() => setStatus(r.id, "completed")}>
                      Complete
                    </Button>
                    <Button variant="danger" onClick={() => setStatus(r.id, "cancelled")}>
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
