# Implementation Phases

Ordered by dependency and risk. Each phase has a clear entry condition, deliverables, and exit condition.

---

## Phase 2 — Design system foundation
**Entry**: Q5 answered (CDN vs compiled Tailwind)
**Effort**: ~0.5 day

### Deliverables
- [ ] Move Tailwind from CDN to compiled (`tailwindcss` CLI or Vite)
- [ ] `tailwind.config.js` with brand color tokens and content paths
- [ ] `static/css/main.css` compiled output, served by WhiteNoise
- [ ] `base.html` updated — remove CDN script tag, link compiled CSS
- [ ] Mobile hamburger nav (HTMX toggle, no JS framework)
- [ ] `base.html` polish: skip-to-content link, favicon placeholder

**Exit**: Running dev server shows styled pages with compiled CSS, mobile nav works.

---

## Phase 3 — Home page + public page polish
**Entry**: Phase 2 complete
**Effort**: ~1 day

### Deliverables
- [ ] **Home page** (`pages/home.html`):
  - Hero: headline + subline + primary CTA ("Voir le catalogue")
  - Trust strip: "Fabrication 3j · Livraison France · TVA incluse"
  - Category grid (3 cards linking to catalog categories)
  - Social proof placeholder (Q10 — fill when partner answers)
- [ ] **Catalog list** (`catalog/product_list.html`): mobile-first grid, sticky category sidebar on desktop
- [ ] **Product detail** (`catalog/product_detail.html`): image zoom hint, delivery info box, add-to-cart feedback already works
- [ ] **Login / Register** (`accounts/`): consistent form layout, error states
- [ ] **CGV / Mentions légales**: real page structure (sections, headings) — content TBD

**Exit**: All public pages render correctly on mobile and desktop. Lighthouse performance ≥ 80.

---

## Phase 4 — HTMX micro-interactions
**Entry**: Phase 3 complete
**Effort**: ~0.5 day

### Deliverables
- [ ] Cart badge live-update on "Ajouter au panier" (already partially done — verify and harden)
- [ ] "Ajouté ✓" feedback animation on product detail
- [ ] Flash messages auto-dismiss after 4s (vanilla JS, tiny)
- [ ] Category sidebar: active state preserves scroll position on filter change

**Exit**: Add-to-cart works end-to-end on desktop and mobile without page reload.

---

## Phase 5 — React cart + checkout tunnel
**Entry**: Q1, Q2, Q3, Q14–Q18 answered. Phase 4 complete.
**Effort**: ~2 days

### Setup
- [ ] `frontend/` directory at repo root: `npm create vite@latest frontend -- --template react-swc-ts`
- [ ] `vite.config.ts` outputs to `../static/js/`
- [ ] `tsconfig.json` strict mode enabled
- [ ] `window.CSRF_TOKEN` declared in `src/env.d.ts`, injected in Django template
- [ ] `useCart` hook (`src/hooks/useCart.ts`) — wraps `/api/cart/` (GET, add, update, remove, clear)

### CartDrawer (global, mounted in base.html)
- [ ] Slides in from right on "Ajouter au panier"
- [ ] Shows last added item + cart total + "Voir mon panier" link + "Commander" CTA
- [ ] Closable via overlay click or ✕ button
- [ ] Badge count in nav updates on every add/remove

### CartPage (`/panier/`)
- [ ] `CartItem`: product name, unit price, quantity stepper, remove button, line total
- [ ] `CartSummary`: subtotal, shipping fee (live from API), total, free shipping progress bar
- [ ] Empty cart state with CTA to catalog
- [ ] "Passer la commande" CTA → navigate to address step

### Checkout tunnel (`/commande/`)
- [ ] `CheckoutStepper`: step indicator (3 steps)
- [ ] `AddressStep`: form with validation, option to use saved address (if logged in)
- [ ] `SummaryStep`: read-only recap of items + address + totals
- [ ] `StripeRedirectButton`: POST to `/api/orders/{id}/checkout/`, loading state, redirect to `checkout_url`
- [ ] Guest email field (shown if not authenticated)

### Confirmation (`/commande/<id>/confirmation/`)
- [ ] Success banner with order number
- [ ] "Voir ma commande" link
- [ ] Cart cleared after confirmed

**Exit**: Complete order flow works — add to cart → checkout → Stripe test card → confirmation page.

---

## Phase 6 — Account portal
**Entry**: Phase 3 complete (can run in parallel with Phase 5)
**Effort**: ~0.5 day

### Deliverables
- [ ] **Order list** (`/mes-commandes/`): table with status badge, date, total, link to detail
- [ ] **Order detail** (`/mes-commandes/<id>/`): items, address, status timeline, invoice download link
- [ ] **Profile** (`/mon-compte/`): name, email (read-only), phone edit, saved addresses list
- [ ] Password reset flow: custom template matching site design

**Exit**: Logged-in customer can see all their orders and update their profile.

---

## Phase 7 — CRM interface
**Entry**: Phase 3 complete. CRM API routes already built.
**Effort**: ~1 day

### URL structure
All under `/crm/` prefix — protected by `CRMRequiredMixin` (checks `crm` or `ops` group).

### Deliverables
- [ ] **CRM middleware/mixin**: redirect non-staff to 403 page
- [ ] **Dashboard** (`/crm/`): count cards (orders by status), last 10 orders table
- [ ] **Order list** (`/crm/commandes/`):
  - Filter bar: status dropdown, date range, email search
  - Paginated table: id, customer/guest email, status badge, total, date
  - Status badge colors per `design_system.md`
- [ ] **Order detail** (`/crm/commandes/<id>/`):
  - Full order info (lines, shipping address, Stripe session ID)
  - Status transition buttons (HTMX PATCH to `/api/crm/orders/{id}/status/`)
  - Transition buttons shown/hidden based on current status + allowed transitions
- [ ] **Customer list** (`/crm/clients/`): email search, paginated table
- [ ] **Customer detail** (`/crm/clients/<id>/`):
  - Profile info
  - Address list with inline edit (HTMX)
  - Order history
- [ ] **Address edit** (`/crm/clients/<id>/adresses/<id>/modifier/`): form, HTMX or standard POST

**Exit**: CRM user can find any order, advance its status, and correct a customer's address.

---

## Phase 8 — QA
**Entry**: Phases 5, 6, 7 complete
**Effort**: ~0.5 day

### Checklist
- [ ] Mobile: test on 375px (iPhone SE) and 390px (iPhone 14)
- [ ] Lighthouse: Performance ≥ 80, SEO = 100, Accessibility ≥ 90 on catalog and product pages
- [ ] Cross-browser: Chrome, Safari, Firefox
- [ ] End-to-end: guest checkout → Stripe test card → confirmation
- [ ] End-to-end: registered user checkout → order visible in account portal
- [ ] CRM: status transition all paths (paid → in_production → shipped → delivered)
- [ ] 404 page: custom template
- [ ] No console errors in production build

---

## Phase 9 — V2 configurator placeholder
**Entry**: Phase 3 complete
**Effort**: 2h

### Deliverables
- [ ] On product detail for configurable product type: show "Configurateur disponible prochainement" section with waitlist/contact CTA
- [ ] React component shell `Configurator.jsx` — renders "coming soon" state, ready to be wired in V2
- [ ] Document in `front-end/v2_configurator_notes.md` what fields and SVG logic will be needed

---

## Effort summary

| Phase | Description | Effort |
|-------|-------------|--------|
| 2 | Design system + compiled Tailwind | 0.5d |
| 3 | Home + public page polish | 1d |
| 4 | HTMX interactions | 0.5d |
| 5 | React cart + checkout | 2d |
| 6 | Account portal | 0.5d |
| 7 | CRM interface | 1d |
| 8 | QA | 0.5d |
| 9 | V2 placeholder | 0.25d |
| **Total** | | **~6.25 days** |

*(With AI assistance — realistic estimate at current pace)*
