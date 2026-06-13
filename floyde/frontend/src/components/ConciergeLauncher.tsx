"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { ConciergeRequest } from "@/lib/types";
import { Button, Input, Label } from "./ui";
import { clsx } from "@/lib/clsx";

const STATUS_LABEL: Record<string, string> = {
  queued: "Queued",
  in_progress: "Ruby is on it",
  completed: "Completed",
  cancelled: "Cancelled",
};

export function ConciergeLauncher() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-1.5 rounded-lg border border-amber-300 bg-amber-50 px-3 py-1.5 text-sm font-medium text-amber-800 transition-colors hover:bg-amber-100 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300 dark:hover:bg-amber-950/50"
      >
        <span aria-hidden>✦</span> Concierge
      </button>
      {open && <ConciergeModal onClose={() => setOpen(false)} />}
    </>
  );
}

function ConciergeModal({ onClose }: { onClose: () => void }) {
  const [phone, setPhone] = useState("");
  const [topic, setTopic] = useState("");
  const [requests, setRequests] = useState<ConciergeRequest[]>([]);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<ConciergeRequest | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getProfile()
      .then((p) => setPhone(p.phone))
      .catch(() => {});
    api.conciergeRequests().then(setRequests).catch(() => {});
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const req = await api.requestConcierge({
        phone,
        topic: topic || "booking assistance",
      });
      setDone(req);
      setRequests((r) => [req, ...r]);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not place the request");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-xl border border-zinc-200 bg-white p-6 shadow-xl dark:border-zinc-800 dark:bg-zinc-950"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-1 flex items-center justify-between">
          <h2 className="text-lg font-semibold tracking-tight">
            <span className="text-amber-500">✦</span> Ruby concierge
          </h2>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <p className="mb-4 text-sm text-zinc-500">
          A real person will call to help you book, choose a style, or sort out
          anything else. Premium service.
        </p>

        {done ? (
          <div className="rounded-lg bg-green-50 px-4 py-3 text-sm text-green-700 dark:bg-green-950/40 dark:text-green-400">
            You&apos;re in the queue — Ruby will call <strong>{done.phone}</strong>{" "}
            shortly.
            <div className="mt-1 text-xs opacity-80">Ref {done.request_id}</div>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-3">
            <div>
              <Label>Phone to call</Label>
              <Input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 313 555 0100"
                required
              />
            </div>
            <div>
              <Label>What can we help with?</Label>
              <Input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Booking assistance"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <Button type="submit" className="w-full" disabled={busy}>
              {busy ? "Requesting…" : "Request a call"}
            </Button>
          </form>
        )}

        {requests.length > 0 && (
          <div className="mt-5 border-t border-zinc-100 pt-4 dark:border-zinc-900">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-400">
              Your requests
            </p>
            <ul className="space-y-2">
              {requests.slice(0, 4).map((r) => (
                <li
                  key={r.id}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="truncate text-zinc-600 dark:text-zinc-300">
                    {r.topic}
                  </span>
                  <span
                    className={clsx(
                      "ml-2 shrink-0 rounded-md px-2 py-0.5 text-xs font-medium",
                      r.status === "completed"
                        ? "bg-zinc-100 text-zinc-500 dark:bg-zinc-900"
                        : "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400",
                    )}
                  >
                    {STATUS_LABEL[r.status] ?? r.status}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
