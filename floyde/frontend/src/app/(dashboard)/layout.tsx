"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { isStaff } from "@/lib/roles";
import { ShopProvider } from "@/lib/shop";
import { DashboardNav } from "@/components/DashboardNav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) router.replace("/login");
    else if (!isStaff(user.role)) router.replace("/flex"); // clients → client app
  }, [user, loading, router]);

  if (loading || !user || !isStaff(user.role)) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-zinc-400">
        Loading…
      </div>
    );
  }

  return (
    <ShopProvider>
      <div className="min-h-screen">
        <DashboardNav />
        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
      </div>
    </ShopProvider>
  );
}
