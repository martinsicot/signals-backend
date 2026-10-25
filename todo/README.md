# TODO — Tickets backend restants pour un site fonctionnel

État au : 2026-09-09
Frontend implémenté : catalogue + tunnel Stripe

---

## 🔴 BLOQUANT — À corriger avant tout test du tunnel

| Ticket | Description | Fichiers |
|--------|-------------|----------|
| [BUG-001](BUG-001-guest-checkout-stripe.md) | Guest checkout bloqué (`IsAuthenticated` sur checkout Stripe) | `orders/api/payment_views.py` |
| [BUG-002](BUG-002-stripe-redirect-url.md) | Stripe redirige vers le backend, pas le frontend | `orders/services/payment_service.py` |
| [BUG-003](BUG-003-delai-variant-serializer.md) | Délai fabrication absent des sérialiseurs variant | `catalog/api/serializers.py` |

## 🟠 IMPORTANT — Requis pour un site complet

| Ticket | Description | Fichiers |
|--------|-------------|----------|
| [FEAT-004](FEAT-004-order-status-public.md) | Endpoint public pour page de confirmation (guests) | `orders/api/views.py` |
| [FEAT-005](FEAT-005-tva-prix-ttc.md) | Exposition des prix TTC (obligation légale France) | `catalog/api/serializers.py`, `orders/api/serializers.py` |
| [FEAT-006](FEAT-006-product-search.md) | Recherche produit (`?q=`) — T4.4 backlog | `catalog/api/views.py` |

## 🟡 TESTS — Couverture du tunnel de paiement

| Ticket | Description |
|--------|-------------|
| [TEST-007](TEST-007-stripe-webhook-tests.md) | Tests Stripe webhook (succès + échec + idempotence) — T8.3 |
| [TEST-008](TEST-008-e2e-tunnel-paiement.md) | Tests E2E panier → paiement → confirmation — T8.2, T6.6 |

## 🟢 INFRA — Déploiement et mise en production

| Ticket | Description |
|--------|-------------|
| [INFRA-009](INFRA-009-vps-coolify-dns.md) | VPS Hetzner + Coolify + DNS/SSL — T1.5, T1.6, T1.7 |
| [INFRA-010](INFRA-010-stripe-live-prod.md) | Stripe live + validation prod — T9.1, T9.4, T9.5 |
| [INFRA-011](INFRA-011-backups-snapshots.md) | Backups PostgreSQL + snapshots serveur — T9.2, T9.3 |

---

## Ordre de traitement recommandé

```
BUG-001 → BUG-002 → BUG-003   (corriger les bugs bloquants)
    ↓
FEAT-004 → FEAT-005            (compléter le tunnel)
    ↓
TEST-007 → TEST-008            (valider avec des tests)
    ↓
FEAT-006                       (search, optionnel au lancement)
    ↓
INFRA-009 → INFRA-010 → INFRA-011   (déploiement prod)
```
