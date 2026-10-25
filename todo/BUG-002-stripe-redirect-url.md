# BUG-002 — Stripe success/cancel URL pointe vers le backend

## Priorité
🔴 BLOQUANT

## Problème

Dans `orders/services/payment_service.py`, les URLs de redirection Stripe sont construites depuis le host de la requête backend :

```python
success_url = f"{scheme}://{host}/order/{order_id}/confirmation"
cancel_url  = f"{scheme}://{host}/cart"
```

Si le backend est déployé sur `api.signals.fr` et le frontend sur `signals.fr`, Stripe redirigera le client vers `api.signals.fr/order/42/confirmation` → page 404 ou API JSON brut.

## Solution attendue

Ajouter une variable d'environnement `FRONTEND_BASE_URL` dans les settings :

```python
# settings/base.py
FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", default="http://localhost:3000")
```

Puis utiliser cette URL dans le service :

```python
base = settings.FRONTEND_BASE_URL
success_url = f"{base}/order/{order_id}/confirmation"
cancel_url  = f"{base}/cart"
```

## Fichiers concernés

- `orders/services/payment_service.py` — `create_checkout_session()`
- `orders/api/payment_views.py` — passage des URLs au service
- `signals/settings/base.py` — ajout `FRONTEND_BASE_URL`
- `.env.example` — documenter la variable

## Acceptance criteria

- En dev : `FRONTEND_BASE_URL=http://localhost:3000` → Stripe redirige vers le front local
- En prod : `FRONTEND_BASE_URL=https://signals.fr` → Stripe redirige vers le bon domaine
- La variable est documentée dans `.env.example`
