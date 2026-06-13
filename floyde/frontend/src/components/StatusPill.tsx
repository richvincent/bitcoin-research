import { clsx } from "@/lib/clsx";
import type { BookingStatus } from "@/lib/types";

const STYLES: Record<string, string> = {
  confirmed: "text-green-700 bg-green-50 dark:text-green-400 dark:bg-green-950/40",
  pending: "text-amber-700 bg-amber-50 dark:text-amber-400 dark:bg-amber-950/40",
  completed: "text-zinc-600 bg-zinc-100 dark:text-zinc-300 dark:bg-zinc-900",
  cancelled: "text-red-700 bg-red-50 dark:text-red-400 dark:bg-red-950/40",
  no_show: "text-red-700 bg-red-50 dark:text-red-400 dark:bg-red-950/40",
};

export function StatusPill({ status }: { status: BookingStatus }) {
  return (
    <span
      className={clsx(
        "rounded-md px-2 py-0.5 text-xs font-medium capitalize",
        STYLES[status] ?? STYLES.completed,
      )}
    >
      {status.replace("_", " ")}
    </span>
  );
}
