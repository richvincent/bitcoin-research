// Tiny typed fetch client for the Floyde API.
// Reads the JWT from localStorage so it works from any client component.

import type {
  AmazonRec,
  Barber,
  BarberMatch,
  Booking,
  ClientProfile,
  ClientProfileUpsert,
  ConciergeRequest,
  ConciergeStatus,
  ManagedBooking,
  Offering,
  Order,
  Payment,
  Product,
  Provider,
  ProviderCategory,
  ProviderDetail,
  Review,
  Service,
  Shop,
  ShopReport,
  User,
} from "./types";

const BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

const TOKEN_KEY = "floyde_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const h = new Headers(headers);
  if (!h.has("Content-Type") && rest.body && !(rest.body instanceof URLSearchParams)) {
    h.set("Content-Type", "application/json");
  }
  const token = auth ? getToken() : null;
  if (token) h.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${BASE}${path}`, { ...rest, headers: h });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  // ── auth ──
  async login(email: string, password: string): Promise<string> {
    const form = new URLSearchParams({ username: email, password });
    const data = await request<{ access_token: string }>("/auth/login", {
      method: "POST",
      auth: false,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    return data.access_token;
  },

  signup(body: {
    email: string;
    password: string;
    full_name?: string;
    role?: string;
  }): Promise<User> {
    return request<User>("/auth/signup", {
      method: "POST",
      auth: false,
      body: JSON.stringify(body),
    });
  },

  me(): Promise<User> {
    return request<User>("/auth/me");
  },

  // ── catalog ──
  shops: () => request<Shop[]>("/shops", { auth: false }),
  services: (shopId?: number) =>
    request<Service[]>(`/services${shopId ? `?shop_id=${shopId}` : ""}`, {
      auth: false,
    }),
  barbers: (shopId: number) => request<Barber[]>(`/shops/${shopId}/barbers`, { auth: false }),

  // ── client profile ──
  getProfile: () => request<ClientProfile>("/clients/me/profile"),
  saveProfile: (body: ClientProfileUpsert) =>
    request<ClientProfile>("/clients/me/profile", {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  // ── matching ──
  matchBarbers(params: {
    service_id?: number;
    lat?: number;
    lng?: number;
    shop_id?: number;
    limit?: number;
  }): Promise<BarberMatch[]> {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) q.set(k, String(v));
    });
    return request<BarberMatch[]>(`/matching/barbers?${q.toString()}`);
  },

  // ── bookings ──
  availability: (barberId: number, serviceId: number, count = 6) =>
    request<string[]>(
      `/bookings/availability?barber_id=${barberId}&service_id=${serviceId}&count=${count}`,
    ),
  book: (body: {
    barber_id: number;
    service_id: number;
    start_time: string;
    source?: string;
    notes?: string;
  }) =>
    request<Booking>("/bookings", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  myBookings: () => request<Booking[]>("/bookings"),
  cancelBooking: (id: number) =>
    request<Booking>(`/bookings/${id}/cancel`, { method: "POST" }),

  // ── staff / dashboard ──
  manageSchedule: (shopId?: number) =>
    request<ManagedBooking[]>(
      `/bookings/manage${shopId ? `?shop_id=${shopId}` : ""}`,
    ),
  staffBooking: (body: {
    client_email: string;
    barber_id: number;
    service_id: number;
    start_time: string;
    source?: string;
    notes?: string;
  }) =>
    request<Booking>("/bookings/staff", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  confirmBooking: (id: number) =>
    request<Booking>(`/bookings/${id}/confirm`, { method: "POST" }),
  completeBooking: (id: number) =>
    request<Booking>(`/bookings/${id}/complete`, { method: "POST" }),

  // POS
  charge: (body: {
    shop_id: number;
    amount_cents: number;
    booking_id?: number | null;
    type?: string;
    currency?: string;
  }) =>
    request<{ payment: Payment; client_secret: string | null }>("/pos/charge", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  payments: (shopId?: number) =>
    request<Payment[]>(`/pos/payments${shopId ? `?shop_id=${shopId}` : ""}`),

  // inventory
  products: (shopId: number) =>
    request<Product[]>(`/inventory/products?shop_id=${shopId}`),
  addProduct: (body: {
    shop_id: number;
    name: string;
    brand?: string;
    quantity?: number;
    reorder_threshold?: number;
    cost_cents?: number;
    price_cents?: number;
  }) =>
    request<Product>("/inventory/products", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  reorderSuggestions: (shopId: number) =>
    request<AmazonRec[]>(`/inventory/reorder-suggestions?shop_id=${shopId}`),
  productRecs: (q: string, limit = 5) =>
    request<AmazonRec[]>(
      `/inventory/recommendations?q=${encodeURIComponent(q)}&limit=${limit}`,
    ),

  // setup / management
  createShop: (body: { name: string; slug: string; address?: string }) =>
    request<Shop>("/shops", { method: "POST", body: JSON.stringify(body) }),
  addBarber: (body: {
    user_id: number;
    shop_id: number;
    display_name: string;
    bio?: string;
    specialties?: string[];
  }) =>
    request<Barber>("/shops/barbers", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  createService: (body: {
    shop_id: number;
    name: string;
    duration_minutes: number;
    price_cents: number;
    tags?: string[];
  }) =>
    request<Service>("/services", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // ── marketplace ──
  marketplaceCategories: () =>
    request<string[]>("/marketplace/categories", { auth: false }),
  providers: (params: { category?: string; q?: string; sort?: string } = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v) qs.set(k, String(v));
    });
    const s = qs.toString();
    return request<Provider[]>(`/marketplace/providers${s ? `?${s}` : ""}`, {
      auth: false,
    });
  },
  provider: (id: number) =>
    request<ProviderDetail>(`/marketplace/providers/${id}`, { auth: false }),
  createProvider: (body: {
    name: string;
    category: ProviderCategory;
    description?: string;
    website?: string;
    contact_email?: string;
    location?: string;
  }) =>
    request<Provider>("/marketplace/providers", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  addOffering: (
    providerId: number,
    body: { title: string; description?: string; price_cents?: number | null; unit?: string },
  ) =>
    request<Offering>(`/marketplace/providers/${providerId}/offerings`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  addReview: (
    providerId: number,
    body: { rating: number; title?: string; body?: string },
  ) =>
    request<Review>(`/marketplace/providers/${providerId}/reviews`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // marketplace orders / transactions
  createOrder: (body: {
    provider_id: number;
    items: { offering_id: number; quantity: number }[];
    buyer_shop_id?: number | null;
    notes?: string;
  }) =>
    request<Order>("/marketplace/orders", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  orders: (role: "buyer" | "seller" = "buyer") =>
    request<Order[]>(`/marketplace/orders?role=${role}`),
  fulfillOrder: (id: number) =>
    request<Order>(`/marketplace/orders/${id}/fulfill`, { method: "POST" }),
  cancelOrder: (id: number) =>
    request<Order>(`/marketplace/orders/${id}/cancel`, { method: "POST" }),

  // ── concierge (Ruby) ──
  requestConcierge: (body: { phone: string; topic: string; shop_id?: number | null }) =>
    request<ConciergeRequest>("/concierge/call", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  conciergeRequests: (shopId?: number) =>
    request<ConciergeRequest[]>(
      `/concierge/requests${shopId ? `?shop_id=${shopId}` : ""}`,
    ),
  updateConciergeStatus: (id: number, status: ConciergeStatus) =>
    request<ConciergeRequest>(
      `/concierge/requests/${id}/status?new_status=${status}`,
      { method: "POST" },
    ),
  callConcierge: (id: number) =>
    request<ConciergeRequest>(`/concierge/requests/${id}/call`, {
      method: "POST",
    }),

  // ── reports ──
  report: (shopId: number, days = 30) =>
    request<ShopReport>(`/reports/summary?shop_id=${shopId}&days=${days}`),
};

export { BASE as API_BASE };
