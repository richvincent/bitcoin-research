# Floyde frontend

Minimal, elegant (Linear/Notion-inspired) Next.js client for Floyde. It serves
two audiences, with role-based routing after login (clients → `/flex`,
barbers/owners → `/dashboard`).

**Client app**
- **Auth** — email/password login + signup (JWT stored client-side)
- **Style profile** — preferred styles, products, nuances; powers matching
- **Flex Cut Now** — pick a service → smart-matched barbers (with fit score &
  reasons) → open slots → one-tap book (deposit auto-confirms in stub mode)
- **Bookings** — list + cancel, with status and fit score

**Shop dashboard** (barber/owner)
- **Overview** — today's appointments, live stats, low-stock alert
- **Schedule** — full booking list with confirm / complete / cancel + walk-in
  booking (on behalf of an existing client)
- **POS** — charge service/product/deposit payments, recent-payments ledger
- **Inventory** — track products, low-stock flags, Amazon restock suggestions
- **Setup** — create a shop, add services and team (owner)

A shop switcher in the dashboard nav scopes everything to the selected shop.
Dark/light mode included, no flash on load.

## Stack
- Next.js 15 (App Router) · React 19 · TypeScript
- Tailwind CSS 3 (zero UI-library dependency — primitives in `src/components/ui.tsx`)

## Run

```bash
cd floyde/frontend
cp .env.local.example .env.local      # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev                           # http://localhost:3000
```

Make sure the backend is running and seeded:

```bash
cd ../backend && python -m app.seed && uvicorn app.main:app --reload
```

Then log in with the demo account: **client@floyde.app / password123**.

## Scripts
- `npm run dev` — dev server
- `npm run build` / `npm start` — production build + serve
- `npm run typecheck` — `tsc --noEmit`

## Layout
```
src/
  app/
    layout.tsx            root: AuthProvider + theme bootstrap
    page.tsx              redirect → /flex or /login
    login/page.tsx
    (app)/                client group (guard + nav)
      layout.tsx
      flex/page.tsx       Flex Cut: match + book
      profile/page.tsx    style profile editor
      bookings/page.tsx   list + cancel
    (dashboard)/          staff group (role guard + ShopProvider + nav)
      layout.tsx
      dashboard/page.tsx            overview
      dashboard/schedule/page.tsx   schedule + walk-ins
      dashboard/pos/page.tsx        point of sale
      dashboard/inventory/page.tsx  inventory + Amazon restock
      dashboard/setup/page.tsx      shop / services / team
  components/             ui primitives, navs, ThemeToggle, TagInput, StatusPill
  lib/
    api.ts               typed fetch client (JWT from localStorage)
    auth.tsx             auth context
    roles.ts             role helpers + role-based home path
    shop.tsx             selected-shop context (dashboard)
    format.ts            money/date helpers
    types.ts             wire types mirroring the backend
```

## Not yet built
Marketplace, concierge call UI, PWA manifest + offline, commission/payouts
reporting, per-barber availability editing. The typed API client already
covers most backend endpoints, so these are largely new screens.
