"use client";

import { clsx } from "@/lib/clsx";

/** Read-only or interactive 1–5 star rating. */
export function Stars({
  value,
  onChange,
  size = "sm",
}: {
  value: number;
  onChange?: (v: number) => void;
  size?: "sm" | "lg";
}) {
  const interactive = !!onChange;
  return (
    <span className={clsx("inline-flex", size === "lg" ? "text-xl" : "text-sm")}>
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          disabled={!interactive}
          onClick={() => onChange?.(n)}
          className={clsx(
            interactive && "cursor-pointer transition-transform hover:scale-110",
            !interactive && "cursor-default",
            n <= Math.round(value)
              ? "text-amber-500"
              : "text-zinc-300 dark:text-zinc-700",
          )}
          aria-label={`${n} star${n > 1 ? "s" : ""}`}
        >
          ★
        </button>
      ))}
    </span>
  );
}
