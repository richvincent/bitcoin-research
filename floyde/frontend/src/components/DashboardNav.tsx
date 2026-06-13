"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useShop } from "@/lib/shop";
import { clsx } from "@/lib/clsx";
import { ThemeToggle } from "./ThemeToggle";

const LINKS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/schedule", label: "Schedule" },
  { href: "/dashboard/reports", label: "Reports" },
  { href: "/dashboard/pos", label: "POS" },
  { href: "/dashboard/inventory", label: "Inventory" },
  { href: "/dashboard/marketplace", label: "Market" },
  { href: "/dashboard/concierge", label: "Concierge" },
  { href: "/dashboard/setup", label: "Setup" },
];

export function DashboardNav() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { shops, shopId, setShopId } = useShop();

  return (
    <header className="sticky top-0 z-10 border-b border-zinc-200 bg-white/80 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/80">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="text-sm font-semibold tracking-tight">
            Floyde<span className="text-zinc-400"> · shop</span>
          </Link>
          <nav className="hidden items-center gap-1 sm:flex">
            {LINKS.map((l) => {
              const active =
                l.href === "/dashboard"
                  ? pathname === l.href
                  : pathname.startsWith(l.href);
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  className={clsx(
                    "rounded-lg px-3 py-1.5 text-sm transition-colors",
                    active
                      ? "bg-zinc-100 font-medium text-zinc-900 dark:bg-zinc-900 dark:text-zinc-100"
                      : "text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100",
                  )}
                >
                  {l.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          {shops.length > 0 && (
            <select
              value={shopId ?? ""}
              onChange={(e) => setShopId(Number(e.target.value))}
              className="rounded-lg border border-zinc-200 bg-white px-2 py-1.5 text-sm text-zinc-700 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-200"
            >
              {shops.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          )}
          <ThemeToggle />
          {user && (
            <button
              onClick={logout}
              className="hidden text-sm text-zinc-500 hover:text-zinc-900 sm:block dark:text-zinc-400 dark:hover:text-zinc-100"
            >
              Sign out
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
