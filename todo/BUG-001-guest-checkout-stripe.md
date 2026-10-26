# BUG-001 — Guest checkout bloqué par IsAuthenticated

## Statut
DONE ✅

## Priorité
🔴 BLOQUANT

## Problème

`CreateCheckoutSessionView` (orders/api/payment_views.py) utilise `IsAuthenticated` comme permission class.

Or `CreateOrderView` est `AllowAny` — un invité peut créer une commande avec son email mais ne peut **pas** ensuite lancer le checkout Stripe. Le tunnel est cassé pour tous les utilisateurs non connectés.

## Comportement actuel

```
POST /api/orders/          → 201 OK  (AllowAny, guest avec email)
POST /api/orders/42/checkout/ → 401 Unauthorized  ← BLOQUANT
```

## Solution attendue

Deux options :

**Option A (recommandée)** — Autoriser le checkout guest via `AllowAny` en ajoutant une validation par `guest_email` ou `order_id + email` :
- Changer permission en `AllowAny`
- Vérifier que l'utilisateur est soit le propriétaire (auth) soit le guest via l'email fourni à la création

**Option B** — Forcer l'authentification avant checkout :
- Côté frontend, rediriger vers login si pas connecté avant d'appeler `/checkout/`
- Plus simple mais exclut la vente sans compte

## Fichiers concernés

- `orders/api/payment_views.py` — `CreateCheckoutSessionView.permission_classes`
- `orders/api/views.py` — logique de validation guest

## Acceptance criteria

- Un utilisateur invité peut créer une commande et payer via Stripe sans créer de compte
- Un utilisateur connecté peut toujours payer
- Une tentative de checkout sur une commande qui n'appartient pas à l'utilisateur retourne 403
