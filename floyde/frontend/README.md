# Floyde frontend

Minimal, elegant (Linear/Notion-inspired) Next.js client for Floyde. Phase 1
covers the headline **client** experience:

- **Auth** — email/password login + signup (JWT stored client-side)
- **Style profile** — preferred styles, products, nuances; powers matching
- **Flex Cut Now** — pick a service → smart-matched barbers (with fit score &
  reasons) → open slots → one-tap book (deposit auto-confirms in stub mode)
- **Bookings** — list + cancel, with status and fit score

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
    (app)/                authenticated group (guard + nav)
      layout.tsx
      flex/page.tsx       Flex Cut: match + book
      profile/page.tsx    style profile editor
      bookings/page.tsx   list + cancel
  components/             ui primitives, Nav, ThemeToggle, TagInput
  lib/
    api.ts               typed fetch client (JWT from localStorage)
    auth.tsx             auth context
    types.ts             wire types mirroring the backend
```

## Not yet built
Barber/owner dashboard, POS UI, marketplace, inventory/Amazon screens,
PWA manifest + offline, concierge call UI. The API client already covers
much of the backend, so these are mostly new screens.
