# Website Brief (EN) — for wireframing

## Website purpose

E-commerce platform selling road traffic signage (panneaux de signalisation) directly online — initially to French individuals, small construction sites, and public bodies (town halls, municipal unions). Launch market is France only, but architecture should anticipate other countries later.

## Core pages

- Homepage
- Catalog (filterable by category, usage, format, material)
- Product detail page
- Configurator (for customizable signs)
- Cart / Checkout / Payment
- Customer account (order tracking)
- Institutional pages (About, Terms, Contact, FAQ)

## Catalog model

Organized by **country**, not by product with variants — a French "stop" sign and a Spanish "stop" sign are treated as two separate products, each with their own catalog hierarchy:

```
Country → Category (danger, obligation, information, town/city signs) → Product → variants + configurable fields
```

## Three product types

Each may need a distinct UI pattern:

1. **Fixed product with variants** — e.g. danger/stop/yield signs. Simple selection of predefined options (size S/M/L, material, reflective class). No free text input.
2. **Configurable product** — e.g. town name signs, street signs. Free-text fields (city name, population, coat of arms/logo), with a **real-time visual preview** (this is the centerpiece feature — likely rendered as dynamic SVG). Price may vary based on content.
3. **Quote-based product** — for highly specific requests or large quantities. Just a contact form, lower priority for launch.

## Key UX priority

The configurator with live SVG preview is the standout selling point — worth the most wireframing attention (input fields on one side, live visual render on the other, similar to product customizer patterns).

## Tone / audience

Mix of B2C (individuals, small worksites) and B2G (municipalities) — so the design should feel both approachable and credible/professional enough for public-sector buyers issuing purchase orders.
