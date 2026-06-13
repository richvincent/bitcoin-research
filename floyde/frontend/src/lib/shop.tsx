"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api } from "./api";
import type { Shop } from "./types";

interface ShopState {
  shops: Shop[];
  shop: Shop | null;
  shopId: number | null;
  setShopId: (id: number) => void;
  loading: boolean;
  refresh: () => void;
}

const ShopContext = createContext<ShopState | null>(null);
const KEY = "floyde_shop_id";

export function ShopProvider({ children }: { children: ReactNode }) {
  const [shops, setShops] = useState<Shop[]>([]);
  const [shopId, setShopIdState] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api
      .shops()
      .then((s) => {
        setShops(s);
        setShopIdState((current) => {
          if (current && s.some((x) => x.id === current)) return current;
          const saved = Number(localStorage.getItem(KEY));
          if (saved && s.some((x) => x.id === saved)) return saved;
          return s[0]?.id ?? null;
        });
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  function setShopId(id: number) {
    setShopIdState(id);
    try {
      localStorage.setItem(KEY, String(id));
    } catch {
      /* ignore */
    }
  }

  const value = useMemo<ShopState>(
    () => ({
      shops,
      shopId,
      shop: shops.find((s) => s.id === shopId) ?? null,
      setShopId,
      loading,
      refresh: load,
    }),
    [shops, shopId, loading],
  );

  return <ShopContext.Provider value={value}>{children}</ShopContext.Provider>;
}

export function useShop(): ShopState {
  const ctx = useContext(ShopContext);
  if (!ctx) throw new Error("useShop must be used within ShopProvider");
  return ctx;
}
