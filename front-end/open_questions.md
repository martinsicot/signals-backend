# Open Questions

Questions that need answers before or during each phase. Grouped by who can answer.

---

## You (Martin) can decide

| # | Question | Blocks | Decision |
|---|----------|--------|----------|
| Q1 | Do you want a cart **drawer** (slides in from right) or a **dedicated cart page** at `/panier/`? | Phase 5 | ✅ **Both** — drawer for quick add feedback, `/panier/` full page for review |
| Q2 | Should the checkout be a **multi-step flow** (address → summary → payment) or a **single long page**? | Phase 5 | ✅ **Multi-step flow** |
| Q3 | Guest checkout: should the address form ask for email inline, or redirect to a "guest vs account" choice screen? | Phase 5 | ✅ **Inline email** — no gate screen, fewer clicks, better conversion |
| Q4 | Do you want a **mobile hamburger menu**, or is the current inline nav enough at mobile sizes? | Phase 3 | ✅ **Hamburger menu** on mobile |
| Q5 | Tailwind CDN → compiled build: do you want **npm** in this repo, or keep it CDN for V1 and compile later? | Phase 2 | ✅ **npm** — compile now |
| Q6 | For the CRM, should status transition buttons be **inline HTMX** on the order list, or only available on the order detail page? | Phase 7 | ✅ **List row** — inline quick-action per row for speed |
| Q7 | Should the home page have a **search bar**? (backend has no search endpoint yet) | Phase 3 | ✅ **Yes** — needs search API endpoint to be built first |
| Q8 | What's the site's **brand name** displayed in the header? Currently "Signals" — is that final? | Phase 2 | ⏳ **Not final** — placeholder for now |

---

## Needs partner / business input

| # | Question | Blocks |
|---|----------|--------|
| Q9 | Do you have a **logo** or wordmark? Otherwise header stays text-only. | Phase 2 |
| Q10 | What **trust signals** go on the home page? (certifications, manufacturer relationship, years in business, delivery promise) | Phase 3 |
| Q11 | Any specific **product photography** style? Signs on white background, in-situ, technical drawing? | Phase 3 |
| Q12 | Is there a **free shipping threshold** that should be prominently shown? (env var exists: `SHIPPING_FREE_THRESHOLD`) | Phase 3 |
| Q13 | Should municipalities (mairies) have a **distinct entry point** on the site? (e.g. "Vous êtes une collectivité ?" section) | Phase 3 |

---

## Technical decisions to make before Phase 5 (React)

| # | Question | Options |
|---|----------|---------|
| Q14 | **React state management** for cart? | (a) `useState` + prop drilling (simple, fine for small tree) · (b) React Context · (c) Zustand. Recommendation: Context — no extra dep, cart state is shallow |
| Q15 | **API calls from React**: plain `fetch` or a library? | (a) native fetch with custom hook · (b) SWR · (c) React Query. Recommendation: native fetch + `useEffect` — no extra dep for V1 |
| Q16 | **CSRF token** passing to React API calls: cookie-based or inject via template? | Inject via `window.CSRF_TOKEN = "{{ csrf_token }}"` in the Django template — simplest |
| Q17 | **React build output location**: `static/js/` (served by Django/WhiteNoise) or a separate CDN? | `static/js/` for V1 — keep infra simple |
| Q18 | **Vite or CRA** for React? | Vite — CRA is deprecated |

---

## V2 configurator (do not block V1 on these)

| # | Question |
|---|----------|
| Q19 | Do SVG source files exist for configurable sign types? What format (SVG, AI, PDF)? |
| Q20 | What fields are configurable per sign? (text lines, commune name, coat of arms image upload, reflective class) |
| Q21 | Should the configurator preview update on every keystroke, or on blur/submit? |
| Q22 | Is the configurator output a PDF quote, an add-to-cart action, or both? |
