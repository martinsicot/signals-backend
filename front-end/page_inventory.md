# Page Inventory

## Legend
| Symbol | Meaning |
|--------|---------|
| ✅ | Template exists, looks good |
| 🔧 | Template exists, needs work |
| ❌ | Missing — must build |
| ⚛️ | React component |
| 🔒 | Auth required |
| 👷 | CRM/staff only |

---

## Public pages (Django templates, SEO-critical)

| URL | Template | Status | Notes |
|-----|----------|--------|-------|
| `/` | `pages/home.html` | 🔧 | Exists but likely bare — needs hero, trust signals, category grid |
| `/catalogue/` | `catalog/product_list.html` | ✅ | Grid + sidebar filters done |
| `/catalogue/<slug>/` | `catalog/product_list.html` | ✅ | Category filter working |
| `/produits/<slug>/` | `catalog/product_detail.html` | ✅ | Detail + JSON-LD + HTMX add-to-cart done |
| `/cgv/` | `pages/cgv.html` | 🔧 | Shell exists — needs real legal content |
| `/mentions-legales/` | `pages/mentions_legales.html` | 🔧 | Shell exists — needs real legal content |
| `/sitemap.xml` | Django sitemap view | ✅ | Already wired |

---

## Account pages (Django templates, auth-gated)

| URL | Template | Status | Notes |
|-----|----------|--------|-------|
| `/connexion/` | `accounts/login.html` | 🔧 | Exists — needs design pass |
| `/inscription/` | `accounts/register.html` | 🔧 | Exists — needs design pass |
| `/mon-compte/` | `accounts/profile.html` | 🔧 | Exists — needs design pass |
| `/mes-commandes/` | `orders/order_list.html` | 🔧 | Exists — needs design pass |
| `/mes-commandes/<id>/` | `orders/order_detail.html` | 🔧 | Exists — needs design pass |
| `/reinitialiser-mot-de-passe/` | Django built-in | ❌ | Need custom template |

---

## Cart + Checkout (React, session-based)

| URL | Component | Status | Notes |
|-----|-----------|--------|-------|
| `/panier/` | `CartPage` ⚛️ | 🔧 | `cart/cart.html` shell exists — replace inner content with React |
| `/commande/adresse/` | `AddressStep` ⚛️ | 🔧 | `orders/checkout.html` shell exists — replace with React multi-step |
| `/commande/recapitulatif/` | `SummaryStep` ⚛️ | ❌ | Part of same React checkout flow |
| _(Stripe hosted page)_ | — | ✅ | Stripe Checkout, no work needed |
| `/commande/<id>/confirmation/` | `orders/confirmation.html` | 🔧 | Shell exists — success state design |

**React mounting strategy**: Django renders the page shell (base.html), React mounts into `<div id="cart-root">` and `<div id="checkout-root">`. State lives in React + calls to `/api/cart/` and `/api/orders/`.

---

## CRM (Django templates, staff-gated)

| URL | Template | Status | Notes |
|-----|----------|--------|-------|
| `/crm/` | `crm/dashboard.html` | ❌ | Order volume summary, quick stats |
| `/crm/commandes/` | `crm/order_list.html` | ❌ | Filterable table (status, date, email) |
| `/crm/commandes/<id>/` | `crm/order_detail.html` | ❌ | Detail + status PATCH via HTMX |
| `/crm/clients/` | `crm/customer_list.html` | ❌ | Search by email |
| `/crm/clients/<id>/` | `crm/customer_detail.html` | ❌ | Profile + addresses + order history |
| `/crm/clients/<id>/adresses/<id>/modifier/` | `crm/address_edit.html` | ❌ | Edit form |

**CRM auth guard**: middleware or mixin checking `request.user.groups` for `crm` or `ops`.

---

## V2 — SVG Configurator (placeholder only in V1)

| URL | Component | Status | Notes |
|-----|-----------|--------|-------|
| `/produits/<slug>/configurer/` | `Configurator` ⚛️ | ❌ V2 | Real-time SVG preview, text/color fields |

In V1: product detail page shows "Configurateur disponible prochainement" for configurable product type.

---

## Summary counts

| Category | Total | Done | Needs work | Missing |
|----------|-------|------|------------|---------|
| Public (SEO) | 7 | 3 | 4 | 0 |
| Account | 6 | 0 | 5 | 1 |
| Cart/Checkout | 5 | 1 | 3 | 1 |
| CRM | 6 | 0 | 0 | 6 |
| V2 | 1 | 0 | 0 | 1 (deferred) |
| **Total** | **25** | **4** | **12** | **8** |
