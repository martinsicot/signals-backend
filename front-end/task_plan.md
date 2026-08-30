# Task Plan: Frontend — Signals e-commerce

## Goal
Design and build a complete, SEO-ready frontend for a French road signage e-commerce site: Django templates for all public/catalog pages, React for the cart + Stripe checkout tunnel, and a lightweight CRM interface for staff.

## Phases

- [x] Phase 0: Audit existing templates + define stack constraints
- [x] Phase 1: Page inventory, design system decisions, open questions
- [ ] Phase 2: Design system — token definitions, component library choice, base layout polish
- [ ] Phase 3: Django template pages — home, catalog, product detail, account pages
- [ ] Phase 4: HTMX interactions — cart badge, add-to-cart feedback, mobile nav
- [ ] Phase 5: React cart + checkout tunnel — cart drawer/page, address form, order summary, Stripe redirect
- [ ] Phase 6: Account portal — order history, order detail, profile (Django templates)
- [ ] Phase 7: CRM interface — order list + status transitions, customer detail, address edit
- [ ] Phase 8: QA — mobile, SEO audit (Lighthouse), cross-browser
- [ ] Phase 9: V2 placeholder — SVG configurator scaffold (component shell only, no logic)

## Key Questions
→ See open_questions.md for full list

## Pending before Phase 3
- [ ] Q6: CRM status button placement (list vs detail) — decide before Phase 7
- [ ] Q8: Final brand name — placeholder "Signals" in use
- [ ] Q9: Logo / wordmark from partner
- [ ] Backend: `GET /api/products/search/?q=` endpoint needed before home page search bar

## Decisions Made
- **CSS**: Tailwind CSS (already in base.html via CDN → move to compiled build in Phase 2)
- **Interactivity on templates**: HTMX (already wired for add-to-cart)
- **React scope**: cart page + checkout tunnel ONLY (not catalog, not account pages)
- **CRM**: Separate Django templates under `/crm/` — no React, simple server-rendered forms
- **Language**: French UI throughout (labels, error messages, dates)
- **SEO**: Django templates own all crawlable pages — React pages are behind auth or non-indexable
- **V2 configurator**: Plan slot in component tree, build shell only

## Errors Encountered
_(none yet)_

## Status
**Currently in Phase 1 — complete.** Phase 2 (design system) is next.
