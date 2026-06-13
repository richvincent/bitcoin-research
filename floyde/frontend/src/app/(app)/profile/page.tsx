"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Button, Card, Input, Label } from "@/components/ui";
import { TagInput } from "@/components/TagInput";

export default function ProfilePage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [points, setPoints] = useState(0);

  const [phone, setPhone] = useState("");
  const [styles, setStyles] = useState<string[]>([]);
  const [products, setProducts] = useState<string[]>([]);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    api
      .getProfile()
      .then((p) => {
        setPhone(p.phone);
        setStyles(p.preferred_styles);
        setProducts(p.preferred_products);
        setNotes(p.style_notes);
        setPoints(p.loyalty_points);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  async function save() {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      await api.saveProfile({
        phone,
        preferred_styles: styles,
        preferred_products: products,
        style_notes: notes,
        nuances: {},
        photo_urls: [],
      });
      setSaved(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-zinc-400">Loading profile…</p>;
  }

  return (
    <div className="max-w-2xl space-y-8">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Your style profile</h1>
          <p className="mt-1 text-sm text-zinc-500">
            This travels with you and powers smart matching at any shop.
          </p>
        </div>
        <div className="text-right">
          <div className="text-lg font-semibold tabular-nums">{points}</div>
          <div className="text-xs text-zinc-400">loyalty points</div>
        </div>
      </div>

      <Card>
        <div className="space-y-5">
          <div>
            <Label>Preferred styles</Label>
            <TagInput
              value={styles}
              onChange={setStyles}
              placeholder="e.g. skin fade, beard, textured top"
              suggestions={["skin fade", "taper", "beard", "lineup", "textured top", "scissor", "low maintenance"]}
            />
          </div>

          <div>
            <Label>Style notes (nuances your barber should know)</Label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Leave length on top, sensitive skin on the neck, #3 on top / #1 sides…"
              className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-400 focus:outline-none dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100"
            />
          </div>

          <div>
            <Label>Preferred products</Label>
            <TagInput
              value={products}
              onChange={setProducts}
              placeholder="e.g. Suavecito Pomade"
            />
          </div>

          <div>
            <Label>Phone</Label>
            <Input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+1 313 555 0100"
              type="tel"
            />
          </div>

          <div className="flex items-center gap-3">
            <Button onClick={save} disabled={saving}>
              {saving ? "Saving…" : "Save profile"}
            </Button>
            {saved && <span className="text-sm text-green-600">Saved ✓</span>}
            {error && <span className="text-sm text-red-600">{error}</span>}
          </div>
        </div>
      </Card>
    </div>
  );
}
