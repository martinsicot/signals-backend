# Design System

## Constraints
- Tailwind CSS (already in use — move from CDN to compiled with Vite)
- No component library imposed — use Tailwind + headless primitives (Headless UI or Radix) for React parts
- HTMX for lightweight Django template interactivity
- French language throughout — no English strings in UI
- **React parts written in TypeScript (TSX)** — strict mode enabled

---

## Brand direction

**Product**: road traffic signs — official, regulated, serious. The site must feel trustworthy and professional, not playful. Think: government-adjacent utility with clean modern execution.

**Tone**: Clear, direct, no marketing fluff. Municipalities and worksites need to find and order quickly.

---

## Color palette

| Token | Hex | Usage |
|-------|-----|-------|
| `brand-blue` | `#1D4ED8` (blue-700) | Primary CTA, links, active states — already in use |
| `brand-blue-dark` | `#1E40AF` (blue-800) | Hover state |
| `brand-blue-light` | `#EFF6FF` (blue-50) | Active nav background, subtle highlights |
| `signal-red` | `#DC2626` (red-600) | Danger, stop signs, destructive actions |
| `signal-orange` | `#D97706` (amber-600) | Warning badges, attention states |
| `signal-yellow` | `#FCD34D` (yellow-300) | Accent only — never for text |
| `neutral-900` | `#111827` | Body text |
| `neutral-500` | `#6B7280` | Secondary text, labels |
| `neutral-200` | `#E5E7EB` | Borders, dividers |
| `neutral-50` | `#F9FAFB` | Card backgrounds, form fields |
| `success` | `#16A34A` (green-600) | In-stock badge, success messages |

**Note**: signal colors (red/orange/yellow) are used sparingly for semantic meaning only — they're not decorative.

---

## Typography

| Role | Class | Detail |
|------|-------|--------|
| Page title (h1) | `text-2xl font-bold` | 24px, semi-bold |
| Section heading (h2) | `text-xl font-semibold` | 20px |
| Card title | `text-sm font-medium` | 14px |
| Body | `text-sm text-gray-600` | 14px, gray-600 |
| Label / meta | `text-xs text-gray-400 uppercase tracking-wide` | 12px |
| Price | `text-3xl font-bold` | 30px, on product detail |
| Price (card) | `text-sm font-semibold` | 14px, on catalog card |

Font: system font stack (no custom font for V1 — faster LCP).

---

## Spacing & layout

- Max content width: `max-w-6xl` (72rem) — already in base.html
- Page padding: `px-4` mobile, implicit on desktop
- Section gap: `py-8` standard, `py-16` for hero sections
- Card gap in grid: `gap-5`
- Form field gap: `space-y-4`

---

## Component catalogue

### Shared (Django templates + React)

| Component | Type | Notes |
|-----------|------|-------|
| `ProductCard` | Template partial | Image, name, dimensions, price, hover shadow |
| `CategorySidebar` | Template partial | Active state on current category |
| `Breadcrumb` | Template partial | Home › Category › Product |
| `Badge` | Template partial | In-stock (green), Production delay (gray) |
| `FlashMessage` | Template partial | Success/error, dismissible, already in base.html |
| `Pagination` | Template partial | Prev/next, page counter |

### React only (cart + checkout)

| Component | Notes |
|-----------|-------|
| `CartItem` | Line with quantity stepper, remove button, subtotal |
| `CartSummary` | Subtotal, shipping fee, total — live update |
| `CartPage` | Full page — list of CartItems + CartSummary + CTA |
| `AddressForm` | Controlled form, validation, reuse saved addresses |
| `CheckoutStepper` | Step indicator: Cart → Address → Summary → Payment |
| `OrderSummary` | Read-only order recap before Stripe redirect |
| `StripeRedirectButton` | Calls `/api/orders/{id}/checkout/`, redirects to `checkout_url` |
| `ConfirmationBanner` | Post-payment success state |

### CRM only (Django templates + HTMX)

| Component | Notes |
|-----------|-------|
| `OrderTable` | Sortable, filterable by status, pagination |
| `StatusBadge` | Color-coded: pending (gray), paid (blue), in_production (yellow), shipped (purple), delivered (green), cancelled (red) |
| `StatusTransitionButton` | HTMX PATCH to `/api/crm/orders/{id}/status/` |
| `CustomerTable` | Search by email, link to detail |
| `AddressEditForm` | Inline HTMX form on customer detail page |

---

## Form conventions

- Labels above inputs always (no placeholder-as-label)
- Error message below field in `text-xs text-red-600`
- Required fields: no asterisk — all fields are required unless marked "(optionnel)"
- Submit button: full-width on mobile, `w-full md:w-auto` on desktop
- Loading state: button disabled + spinner icon during async operations

---

## Tailwind build setup (Phase 2 decision)

Move from CDN to compiled:
```
npm install -D tailwindcss @tailwindcss/forms
npx tailwindcss init
```

Output: `static/css/main.css` — served by WhiteNoise in production.

For React: Vite + `@vitejs/plugin-react-swc` (faster than Babel), TypeScript strict mode, output into `static/js/`.
Django's `{% static %}` tag serves bundles. No webpack.

```
npm create vite@latest frontend -- --template react-swc-ts
```

Key config:
- `tsconfig.json`: `"strict": true`, `"jsx": "react-jsx"`
- `vite.config.ts`: `build.outDir = "../static/js"`, `build.emptyOutDir = true`
- `.tsx` for all components, `.ts` for hooks and utilities

---

## Responsive breakpoints

| Breakpoint | Width | Key changes |
|------------|-------|-------------|
| mobile (default) | < 768px | Single column, sidebar hidden, hamburger nav |
| `md` | ≥ 768px | Two-column catalog, sidebar visible, full nav |
| `lg` | ≥ 1024px | Three-column catalog grid |

Mobile is primary — most B2C traffic will be mobile. Municipalities ordering in bulk will use desktop.
