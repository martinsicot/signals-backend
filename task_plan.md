# Task Plan: Backend Features — État des lieux & Reste à faire

## Goal
Identifier ce qui manque côté backend pour que le V1 soit prêt à livrer au frontend et passer en production.

## Status
**Audit complet** — plan à jour au 2026-09-06

---

## Ce qui est DONE ✅

### Auth & Accounts
- [x] Modèles User / Customer / Address
- [x] Register, Login, Logout, Me
- [x] Password reset (request + confirm)
- [x] Addresses CRUD (customer-facing)
- [x] CRM endpoints (list customers, addresses)

### Catalog
- [x] Modèles Category / Product / ProductVariant / PriceSchedule / PriceCell
- [x] Import grille de prix (`import_price_grid`)
- [x] Link images (`link_product_images`)
- [x] Génération thumbnails WebP (`generate_thumbnails`)
- [x] GET /api/categories/
- [x] GET /api/products/ (?category, ?q)
- [x] GET /api/products/<slug>/
- [x] GET /api/variants/<id>/
- [x] URLs media absolues dans les réponses API

### Cart
- [x] Cart session-based (guest + auth)
- [x] GET /api/cart/
- [x] POST /api/cart/add/
- [x] PATCH /api/cart/update/<variant_id>/
- [x] DELETE /api/cart/remove/<variant_id>/
- [x] DELETE /api/cart/clear/
- [x] Calcul frais de port (SHIPPING_FREE_THRESHOLD / SHIPPING_FEE)

### Orders
- [x] Modèles Order / OrderLine avec snapshots
- [x] Domaine pur (dataclasses, règles, exceptions)
- [x] POST /api/orders/ (auth + guest)
- [x] GET /api/orders/mine/
- [x] GET /api/orders/<id>/
- [x] POST /api/orders/<id>/checkout/ → Stripe session
- [x] POST /api/webhooks/stripe/ (completed / expired / failed)
- [x] CRM orders (list, detail, status update)

### Notifications
- [x] Email confirmation commande (HTML + texte)
- [x] Email confirmation paiement + PDF facture (WeasyPrint)
- [x] Tâches Celery async

### Infra
- [x] Dockerfile + docker-compose
- [x] render.yaml (branch: master)
- [x] Settings dev / prod
- [x] Health check /health/
- [x] Swagger /api/docs/
- [x] Serving media en prod (suppression garde DEBUG)
- [x] Handler 404/500 JSON

---

## Ce qui MANQUE côté backend ❌

### Priorité HAUTE — bloquant pour le frontend

- [ ] **Adresses guest au checkout**
  Le endpoint `POST /api/orders/` attend une `shipping_address` mais il n'y a pas
  de validation explicite du format ni de création d'adresse pour les guests.
  À clarifier / documenter proprement.

- [ ] **Pagination sur les list endpoints**
  `GET /api/products/` peut retourner 1832 produits d'un coup.
  DRF pagination configurée globalement (PAGE_SIZE=20) mais pas activée sur
  les vues catalog (elles héritent `APIView`, pas `ListAPIView`).

- [ ] **Filtres avancés catalog**
  Actuellement uniquement `?category` et `?q`. Pas de filtre par :
  - shape (triangle, rond, carré…)
  - taille
  - classe (CL1/CL2)
  Utile pour le frontend catalogue.

- [ ] **Endpoint prix variants dynamique**
  Pour le configurateur, le frontend a besoin de récupérer le prix d'un variant
  par (product_slug, taille, classe, backing) sans connaître l'ID du variant.
  Actuellement `GET /api/variants/<id>/` mais l'ID n'est pas connu a priori.

### Priorité MOYENNE

- [ ] **Tests Stripe webhook** (T8.3)
  Cas succès + échec + session expirée. À compléter.

- [ ] **Tests e2e cart → order → payment** (T8.2)
  Flow complet non couvert.

- [ ] **Permissions CRM** — `IsCRM` / `IsOps` à solidifier
  Role separation actuellement vérifiée manuellement dans les vues.

### Priorité BASSE (post-V1)

- [ ] Configurateur / devis (quote products) — hors scope V1
- [ ] Multi-language catalog (/fr/, /es/) — architecture prévue, non implémentée
- [ ] Backups Postgres automatiques
- [ ] Stripe live mode

---

## Décisions prises
- Stack Render (pas Coolify/Hetzner) pour le moment
- Images baked dans Docker, pas de Cloudflare R2 encore
- `import_price_grid --clear` à chaque deploy (DB toujours propre)
- Frontend séparé (Vercel), CORS à configurer via `CORS_ALLOWED_ORIGINS`
