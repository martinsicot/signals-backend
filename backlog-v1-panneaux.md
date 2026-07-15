# Backlog V1 — Site e-commerce panneaux de signalisation

Scope V1 : vente en ligne aux particuliers uniquement, paiement Stripe Checkout, sans devis collectivités, sans configurateur temps réel, sans automatisation Celery poussée.

Estimation totale : ~7-9 jours-homme effectifs avec IA.

---

## EPIC 1 — Setup projet & infra (≈1j)

- [x] **T1.1** — Init projet Django (structure apps : `catalog`, `orders`, `accounts`) — *uv + pyproject.toml*
- [x] **T1.2** — Config Docker + docker-compose local (Django, Postgres, Redis) — *avec healthchecks*
- [x] **T1.3** — Config `.env` / settings (dev, prod) avec `django-environ`
- [x] **T1.4** — Setup `.gitignore` + `.python-version` + `Dockerfile` prod
- [ ] **T1.5** — Provisionner VPS Hetzner (CX22) + installer Coolify
- [ ] **T1.6** — Connecter repo à Coolify, premier déploiement "Hello World"
- [ ] **T1.7** — Config domaine + DNS + SSL (Let's Encrypt via Coolify)

---

## EPIC 2 — Modèles de données & Django Admin (≈1.5-2j)

- [x] **T2.1** — Modèle `Product` (nom, description, prix, dimensions, matériau, image, slug SEO)
- [ ] **T2.2** — Modèle `ProductVariant` — *reporté V2, scope non confirmé avec l'associé*
- [x] **T2.3** — Modèle `Category`
- [x] **T2.4** — Modèle `Customer` (particulier — nom, email, téléphone)
- [x] **T2.5** — Modèle `Address` (livraison/facturation)
- [x] **T2.6** — Modèle `Order` + `OrderLine` (statuts : pending, paid, in_production, shipped, delivered, cancelled)
- [x] **T2.7** — Config Django Admin pour `Product`/`Category`
- [x] **T2.8** — Config Django Admin pour `Order` (vue liste + détail + inline lines)
- [x] **T2.9** — Migrations + seed data de test — *management command `seed_data` (8 produits, 3 catégories)*

---

## EPIC 3 — Authentification (≈1j)

- [x] **T3.1** — Inscription / connexion particulier (Django auth natif, API DRF)
- [x] **T3.2** — Mot de passe oublié / reset — *POST /api/auth/password-reset/ + confirm/*
- [x] **T3.3** — Mode "commande invité" (sans compte, juste email) — *guest_email sur OrderModel*
- [x] **T3.4** — Endpoint "mes commandes" (historique pour compte connecté)

---

## EPIC 4 — Catalogue & fiches produit (≈1.5-2j)

- [x] **T4.1** — Page listing produits — *Django template + grille + pagination*
- [x] **T4.2** — Filtres par catégorie — *sidebar statique, navigation par slug*
- [x] **T4.3** — Page fiche produit — *Django template, add-to-cart via htmx*
- [ ] **T4.4** — Recherche produit basique
- [x] **T4.5** — SEO on-page — *meta title/description dynamiques + schema.org/Product sur fiche*
- [x] **T4.6** — Sitemap.xml dynamique — *django.contrib.sitemaps, products + categories*
- [x] **T4.7** — Page catégorie — *même vue ProductListView filtrée par slug*

---

## EPIC 5 — Panier & tunnel de commande (≈1.5-2j)

- [x] **T5.1** — Logique panier — *session Django (invité + connecté), app `cart/` avec Cart class + API REST*
- [ ] **T5.2** — Vue panier HTML (ajout, modification quantité, suppression) — *React*
- [ ] **T5.3** — Formulaire adresse de livraison / facturation — *React*
- [x] **T5.4** — Calcul frais de livraison — *domain rule `compute_shipping_fee()`, seuil configurable via env*
- [ ] **T5.5** — Page récapitulatif avant paiement — *React*
- [ ] **T5.6** — Validation des stocks/délais avant passage en paiement (affichage délai fabrication 3j)

---

## EPIC 6 — Paiement Stripe (≈1-1.5j)

- [x] **T6.1** — Config compte Stripe — *clés dans `.env.example`, settings prêts*
- [x] **T6.2** — Création session Stripe Checkout — *POST /api/orders/{id}/checkout/*
- [x] **T6.3** — Webhook `checkout.session.completed` → mark_as_paid + email
- [x] **T6.4** — Webhook gestion échec paiement / expiration → CANCELLED
- [ ] **T6.5** — Page confirmation commande (post-paiement) — *React*
- [ ] **T6.6** — Tests en mode Stripe test (carte test, webhook local avec Stripe CLI)

---

## EPIC 7 — Emails & notifications (≈0.5-1j)

- [x] **T7.1** — Config SMTP — *EMAIL_BACKEND configurable via env, console par défaut en dev*
- [x] **T7.2** — Email confirmation commande — *Celery task `send_order_confirmation` au moment de create_order*
- [x] **T7.3** — Email confirmation paiement — *Celery task `send_payment_confirmation` au webhook Stripe*
- [x] **T7.4** — Notification email admin — *envoyée en même temps que T7.3*
- [x] **T7.5** — Génération facture PDF (WeasyPrint) — *jointe à l'email de confirmation de paiement*

---

## EPIC 8 — Tests & QA (≈1-1.5j)

- [x] **T8.1** — Tests domain (calcul totaux, frais de port, validation quantité) — *pytest, sans DB*
- [x] **T8.1b** — Tests services (create_order, cas d'erreur) — *mocks, sans DB*
- [x] **T8.1c** — Tests API orders, accounts, catalog — *intégration DRF*
- [x] **T8.1d** — Tests Cart class — *session-based, sans DB*
- [ ] **T8.2** — Tests parcours complet panier → paiement → confirmation
- [ ] **T8.3** — Tests webhook Stripe (cas succès + échec)
- [ ] **T8.4** — Test manuel cross-browser / mobile du tunnel de commande
- [x] **T8.5** — RGPD basique — *pages CGV + mentions légales avec contenu*

---

## EPIC 9 — Mise en prod (≈0.5-1j)

- [ ] **T9.1** — Bascule Stripe en mode live + clés prod
- [ ] **T9.2** — Config backups Postgres automatiques (Coolify + Hetzner Object Storage)
- [ ] **T9.3** — Snapshot serveur Hetzner activé
- [ ] **T9.4** — Vérification finale SSL, DNS, emails en prod
- [ ] **T9.5** — Commande de test réelle (petit montant) pour valider le tunnel end-to-end

---

## Hors scope V1 (à garder pour V2)
- Parcours devis / collectivités
- Configurateur de panneau temps réel (React)
- Automatisations Celery (relances, transmission fournisseur auto, statut fabrication live)
- Comptes multi-utilisateurs (mairies)
- Facturation automatisée avancée / export compta
