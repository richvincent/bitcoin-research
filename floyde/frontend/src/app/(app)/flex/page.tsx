"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { BarberMatch, Service } from "@/lib/types";
import { Badge, Button, Card } from "@/components/ui";
import { clsx } from "@/lib/clsx";

// Default to the demo shop's neighborhood (Detroit) when geolocation isn't used.
const DEFAULT_LOC = { lat: 42.3314, lng: -83.0458 };

function dollars(cents: number) {
  return `$${(cents / 100).toFixed(0)}`;
}

function formatSlot(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    weekday: "short",
    hour: "numeric",
    minute: "2-digit",
    month: "short",
    day: "numeric",
  });
}

export default function FlexPage() {
  const router = useRouter();
  const [services, setServices] = useState<Service[]>([]);
  const [serviceId, setServiceId] = useState<number | null>(null);
  const [loc, setLoc] = useState(DEFAULT_LOC);
  const [matches, setMatches] = useState<BarberMatch[] | null>(null);
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .services()
      .then((s) => {
        setServices(s);
        if (s.length) setServiceId(s[0].id);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load services"));
  }, []);

  async function findBarbers() {
    if (!serviceId) return;
    setLoadingMatches(true);
    setError(null);
    setMatches(null);
    try {
      const m = await api.matchBarbers({
        service_id: serviceId,
        lat: loc.lat,
        lng: loc.lng,
        limit: 8,
      });
      setMatches(m);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Matching failed");
    } finally {
      setLoadingMatches(false);
    }
  }

  function useMyLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        setLoc({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setLoc(DEFAULT_LOC),
    );
  }

  const selectedService = services.find((s) => s.id === serviceId);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Flex Cut Now</h1>
        <p className="mt-1 text-sm text-zinc-500">
          We match you to the right barber by your style, distance, rating, and who&apos;s
          open soonest.
        </p>
      </div>

      <Card>
        <div className="space-y-4">
          <div>
            <p className="mb-2 text-sm font-medium text-zinc-700 dark:text-zinc-300">
              What are you after?
            </p>
            <div className="flex flex-wrap gap-2">
              {services.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setServiceId(s.id)}
                  className={clsx(
                    "rounded-lg border px-3.5 py-2 text-left text-sm transition-colors",
                    serviceId === s.id
                      ? "border-zinc-900 bg-zinc-900 text-white dark:border-white dark:bg-white dark:text-zinc-900"
                      : "border-zinc-200 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900",
                  )}
                >
                  <span className="font-medium">{s.name}</span>
                  <span
                    className={clsx(
                      "ml-2",
                      serviceId === s.id ? "opacity-70" : "text-zinc-400",
                    )}
                  >
                    {dollars(s.price_cents)} · {s.duration_minutes}m
                  </span>
                </button>
              ))}
              {!services.length && (
                <p className="text-sm text-zinc-400">
                  No services yet — seed the backend (<code>python -m app.seed</code>).
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={findBarbers} disabled={!serviceId || loadingMatches}>
              {loadingMatches ? "Matching…" : "Find my barber"}
            </Button>
            <button
              onClick={useMyLocation}
              className="text-sm text-zinc-500 underline-offset-2 hover:underline"
            >
              Use my location
            </button>
            <span className="text-xs text-zinc-400">
              near {loc.lat.toFixed(2)}, {loc.lng.toFixed(2)}
            </span>
          </div>
        </div>
      </Card>

      {error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600 dark:bg-red-950/40">
          {error}
        </p>
      )}

      {matches && (
        <div className="space-y-3">
          <p className="text-sm text-zinc-500">
            {matches.length} {matches.length === 1 ? "match" : "matches"}
          </p>
          {matches.map((m) => (
            <MatchRow
              key={m.barber.id}
              match={m}
              service={selectedService}
              onBooked={() => router.push("/bookings")}
            />
          ))}
          {!matches.length && (
            <p className="text-sm text-zinc-400">
              No barbers available right now. Try another service or check back soon.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function MatchRow({
  match,
  service,
  onBooked,
}: {
  match: BarberMatch;
  service: Service | undefined;
  onBooked: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [slots, setSlots] = useState<string[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadSlots() {
    if (!service) return;
    setOpen((o) => !o);
    if (slots) return;
    try {
      setSlots(await api.availability(match.barber.id, service.id, 6));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load times");
    }
  }

  async function book(slot: string) {
    if (!service) return;
    setBusy(true);
    setError(null);
    try {
      await api.book({
        barber_id: match.barber.id,
        service_id: service.id,
        start_time: slot,
        source: "flex",
      });
      onBooked();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Booking failed");
      setBusy(false);
    }
  }

  return (
    <Card>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-medium">{match.barber.display_name}</h3>
            <Badge>{match.barber.rating.toFixed(1)}★</Badge>
          </div>
          <p className="mt-0.5 text-sm text-zinc-500">{match.shop.name}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {match.reasons.slice(0, 4).map((r, i) => (
              <span
                key={i}
                className="rounded-md bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600 dark:bg-zinc-900 dark:text-zinc-400"
              >
                {r}
              </span>
            ))}
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="text-right">
            <div className="text-lg font-semibold tabular-nums">
              {Math.round(match.score * 100)}
            </div>
            <div className="text-xs text-zinc-400">fit score</div>
          </div>
          <Button variant="ghost" onClick={loadSlots}>
            {open ? "Hide times" : "Book"}
          </Button>
        </div>
      </div>

      {open && (
        <div className="mt-4 border-t border-zinc-100 pt-4 dark:border-zinc-900">
          {error && <p className="mb-2 text-sm text-red-600">{error}</p>}
          {!slots && !error && (
            <p className="text-sm text-zinc-400">Loading times…</p>
          )}
          {slots && (
            <div className="flex flex-wrap gap-2">
              {slots.map((s) => (
                <button
                  key={s}
                  disabled={busy}
                  onClick={() => book(s)}
                  className="rounded-lg border border-zinc-200 px-3 py-1.5 text-sm hover:border-zinc-900 hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-800 dark:hover:border-white dark:hover:bg-zinc-900"
                >
                  {formatSlot(s)}
                </button>
              ))}
              {!slots.length && (
                <p className="text-sm text-zinc-400">No open times this week.</p>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
