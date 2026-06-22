# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Nature of this repository

This is **not a codebase yet** — there is no application code, no build system, no tests, and no dependencies to install. The repo currently contains only planning/strategy markdown documents for a project still in the pre-launch, pre-incorporation stage. Treat this repo as a knowledge base to read before helping with anything (planning, drafting documents, eventually scaffolding the actual app described in `05_archi_technique.md`).

## Project in one paragraph

E-commerce site selling road traffic signage (panneaux de signalisation), sold directly online to French individuals, small worksites, and public bodies (mairies, syndicats). Stock model: the new company only buys from a Czech manufacturer once a customer has already paid online — no inventory risk. Two co-founders: Martin (dev, 10 yrs Django/DRF/React, handles tech/SEO/acquisition) and a potential associate who is an existing signage wholesaler with a direct relationship to the Czech manufacturer (he handles supplier relationship, product/compliance knowledge, supplier orders). As of the last update, the partnership is **not yet formalized** — still in the qualification stage with the associate.

## Document index

Files are numbered to reflect read order / topic grouping. Read them in order when picking up context:

| File | Content |
|---|---|
| `01_contexte_projet.md` | Founder profile, business opportunity, target market, launch phase (side business first) |
| `02_modele_commercial.md` | Legal/financial flow, role split between the two associates, in-house marketing strategy |
| `03_questions_associe.md` | Full list of open questions still to clarify with the associate (legal, product, supplier, logistics, pricing, competition) |
| `04_structure_site.md` | Site structure, catalog model (organized **by country**, not by product variant), the 3 product types (fixed/configurable/quote-based), the configurator concept |
| `05_archi_technique.md` | Target tech stack and architecture (Django+DRF / React / PostgreSQL / Stripe / Cloudflare R2 / Brevo), data model sketch, explicit anti-choices (no Shopify/WooCommerce, not React-everywhere) |
| `06_budget_finances.md` | Infra cost phases, marketing budget, break-even estimate, open financial/tax questions |
| `07_prep_reunion_associe.md` | Prep notes for the first formal meeting with the potential associate — scoped deliberately to qualification only (no capital/legal talk yet) |

## Key state to keep straight across sessions

- **Legal entity does not exist yet.** Don't refer to "the company" as if it's formed — it's a planned new SAS/SARL, contingent on the associate partnership being confirmed.
- **Launch market is France only**, with multi-country architecture (`/fr/`, `/es/`, `/de/`) anticipated but not built.
- **Catalog hierarchy**: Country → Category → Product (fixed / configurable / quote) → variants + configurable fields. A French "stop" sign and a Spanish "stop" sign are separate products, not variants of one.
- **A large set of questions is intentionally unanswered** (capital split, supplier pricing, exact margins, who absorbs shipping loss/damage, etc. — see `03_questions_associe.md` and `06_budget_finances.md`). Don't assume answers to these; flag them as open when relevant.
- The relationship with the associate is currently being **qualified, not negotiated** — sensitive topics (capital, gérance, salaries) are deliberately deferred past the first meeting (see `07_prep_reunion_associe.md`).
- Stack decisions in `05_archi_technique.md` are intentional choices already made (Django+DRF, React only for configurator/catalog/checkout, Stripe, Cloudflare R2, Brevo) — don't propose alternative platforms (e.g. Shopify) without flagging that it contradicts a documented decision.
