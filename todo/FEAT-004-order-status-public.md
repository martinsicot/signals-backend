# FEAT-004 — Endpoint public de statut de commande (page de confirmation)

## Priorité
🟠 IMPORTANT

## Besoin

Après le paiement Stripe, le client est redirigé vers `/order/{id}/confirmation`. Le frontend doit afficher le récapitulatif de la commande et son statut (payée, en attente, etc.).

Actuellement `GET /api/orders/<id>/` requiert `IsAuthenticated`. Un invité qui vient de payer n'a pas de token JWT → impossible d'afficher la page de confirmation.

## Solution attendue

Créer un endpoint public de statut minimal, accessible par l'`order_id` + `guest_email` OU par `stripe_session_id` :

```
GET /api/orders/<id>/status/?email=client@example.com
GET /api/orders/by-session/<stripe_session_id>/
```

Le endpoint doit retourner uniquement les infos nécessaires pour la page de confirmation :
- statut, montant total, email de contact, résumé des lignes (noms produits + quantités)
- PAS les informations sensibles complètes

### Règles d'accès
- Invité : doit fournir l'email associé à la commande → correspond à `guest_email`
- Connecté : doit être le propriétaire (`customer.user == request.user`)

## Fichiers concernés

- `orders/api/views.py` — nouvelle vue `OrderStatusView`
- `orders/api/urls.py` — nouvelle route
- `orders/api/serializers.py` — `OrderStatusSerializer` (sous-ensemble de `OrderSerializer`)

## Acceptance criteria

- `GET /api/orders/42/status/?email=test@ex.com` retourne le statut si l'email correspond
- `GET /api/orders/42/status/?email=wrong@ex.com` retourne 403
- Un utilisateur connecté peut appeler l'endpoint sans email
- Le endpoint est documenté dans Swagger
