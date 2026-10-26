# FEAT-005b — TVA 20% : exposition backend des prix TTC

## Priorité
🟠 IMPORTANT (obligation légale e-commerce France)

## Branche
`feat/FEAT-005b-tva-backend`

## Contexte

La loi française impose l'affichage du prix TTC pour les ventes aux particuliers. Les prix en base de données sont en HT. Le backend doit exposer les valeurs TTC calculées afin que le frontend puisse les afficher sans recalculer côté client (risque d'arrondi, pas de centralisation du taux).

## Fichiers à modifier

### `signals/settings/base.py`
Ajouter la constante centralisée :
```python
from decimal import Decimal
VAT_RATE = Decimal("0.20")
```

### `catalog/api/serializers.py`
- `ProductVariantSerializer` — ajouter `price_ttc` (SerializerMethodField) et renommer `price` → `price_ht` dans les fields
- `ProductListSerializer` — ajouter `min_price_ttc` calculé depuis `min_price`

```python
from django.conf import settings

def get_price_ttc(self, obj):
    if obj.price is None:
        return None
    return round(obj.price * (1 + settings.VAT_RATE), 2)
```

### `orders/api/serializers.py`
- `OrderLineSerializer` — ajouter `unit_price_ttc`
- `OrderSerializer` — ajouter `subtotal_ttc` et `total_ttc`

### `orders/domain/rules.py`
- Vérifier `compute_shipping_fee()` : les frais de port sont-ils HT ou TTC ? Documenter clairement.

## Acceptance criteria

- `GET /api/products/` expose `price_ht` et `price_ttc` sur chaque variant
- `GET /api/products/<slug>/` expose `price_ht` et `price_ttc` sur chaque variant
- `GET /api/orders/mine/` expose `unit_price_ttc`, `subtotal_ttc`, `total_ttc`
- Le taux TVA est lu depuis `settings.VAT_RATE` (pas hardcodé dans les sérialiseurs)
- Les montants envoyés à Stripe restent en TTC × 100 centimes (vérifier `payment_service.py`)

## Dépendances
- Aucune dépendance bloquante
- FEAT-005f (frontend) dépend de ce ticket
