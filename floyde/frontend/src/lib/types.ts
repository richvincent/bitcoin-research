// Wire types mirroring the Floyde backend (app/schemas/schemas.py).

export type UserRole = "client" | "barber" | "owner" | "admin";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface Shop {
  id: number;
  name: string;
  slug: string;
  address: string;
  latitude: number | null;
  longitude: number | null;
  timezone: string;
}

export interface Barber {
  id: number;
  shop_id: number;
  display_name: string;
  bio: string;
  specialties: string[];
  rating: number;
  is_active: boolean;
}

export interface Service {
  id: number;
  shop_id: number;
  name: string;
  description: string;
  duration_minutes: number;
  price_cents: number;
  tags: string[];
  is_active: boolean;
}

export interface ClientProfile {
  id: number;
  user_id: number;
  phone: string;
  preferred_styles: string[];
  style_notes: string;
  nuances: Record<string, unknown>;
  photo_urls: string[];
  preferred_products: string[];
  loyalty_points: number;
}

export interface ClientProfileUpsert {
  phone: string;
  preferred_styles: string[];
  style_notes: string;
  nuances: Record<string, unknown>;
  photo_urls: string[];
  preferred_products: string[];
}

export interface BarberMatch {
  barber: Barber;
  shop: Shop;
  score: number;
  distance_km: number | null;
  next_available: string | null;
  reasons: string[];
}

export type BookingStatus =
  | "pending"
  | "confirmed"
  | "completed"
  | "cancelled"
  | "no_show";

export interface Booking {
  id: number;
  client_id: number;
  barber_id: number;
  shop_id: number;
  service_id: number;
  start_time: string;
  end_time: string;
  status: BookingStatus;
  source: string;
  deposit_cents: number;
  match_score: number | null;
  notes: string;
}
