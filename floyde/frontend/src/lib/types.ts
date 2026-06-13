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

export interface ManagedBooking {
  id: number;
  start_time: string;
  end_time: string;
  status: BookingStatus;
  source: string;
  deposit_cents: number;
  price_cents: number;
  match_score: number | null;
  notes: string;
  client_name: string;
  client_email: string;
  barber_id: number;
  barber_name: string;
  service_name: string;
}

export type PaymentType = "deposit" | "final" | "product";
export type PaymentStatus = "pending" | "succeeded" | "failed" | "refunded";

export interface Payment {
  id: number;
  booking_id: number | null;
  shop_id: number;
  amount_cents: number;
  currency: string;
  type: PaymentType;
  status: PaymentStatus;
  stripe_payment_intent_id: string | null;
}

export interface Product {
  id: number;
  shop_id: number;
  name: string;
  brand: string;
  sku: string;
  quantity: number;
  reorder_threshold: number;
  cost_cents: number;
  price_cents: number;
  amazon_asin: string | null;
}

export interface AmazonRec {
  asin: string;
  title: string;
  brand: string;
  price: string;
  rating: number | null;
  review_count: number | null;
  url: string;
  image_url: string;
}

export type ProviderCategory =
  | "supplies"
  | "equipment"
  | "insurance"
  | "marketing"
  | "education"
  | "finance"
  | "software"
  | "other";

export interface Provider {
  id: number;
  name: string;
  slug: string;
  category: ProviderCategory;
  description: string;
  website: string;
  logo_url: string;
  contact_email: string;
  location: string;
  rating: number;
  review_count: number;
  is_active: boolean;
  created_by: number | null;
}

export interface Offering {
  id: number;
  provider_id: number;
  title: string;
  description: string;
  price_cents: number | null;
  unit: string;
  is_active: boolean;
}

export interface Review {
  id: number;
  provider_id: number;
  author_id: number;
  author_name: string;
  rating: number;
  title: string;
  body: string;
  created_at: string;
}

export interface ProviderDetail extends Provider {
  offerings: Offering[];
  reviews: Review[];
}
