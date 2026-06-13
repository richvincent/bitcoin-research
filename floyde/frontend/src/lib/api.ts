// Tiny typed fetch client for the Floyde API.
// Reads the JWT from localStorage so it works from any client component.

import type {
  Barber,
  BarberMatch,
  Booking,
  ClientProfile,
  ClientProfileUpsert,
  Service,
  Shop,
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
};

export { BASE as API_BASE };
