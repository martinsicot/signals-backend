# FEAT-005 — Exposition des prix TTC (TVA 20%)

## Priorité
🟠 IMPORTANT (obligation légale e-commerce France)

## Contexte

La loi française impose l'affichage du prix TTC pour les ventes aux particuliers. Les prix en base de données sont en HT (`prix_vente_ht`). Le frontend doit pouvoir afficher le prix TTC sans recalculer côté client (risque d'erreur d'arrondi, pas de centralisation du taux TVA).

## Comportement actuel

Les sérialiseurs exposent `price` (qui correspond au HT dénormalisé sur `ProductVariant.price`). Pas de champ TTC ni de taux de TVA.

## Solution attendue

**Option A (recommandée)** — Champ calculé dans le sérialiseur :

```python
class ProductVariantSerializer(serializers.ModelSerializer):
    price_ttc = serializers.SerializerMethodField()

    def get_price_ttc(self, obj):
        return round(obj.price * Decimal("1.20"), 2)
```

Ajouter aussi un champ `vat_rate` (ex: `0.20`) pour que le frontend puisse afficher "dont TVA : X€".

**Option B** — Constante côté settings + exposée via un endpoint `/api/config/` :
```python
VAT_RATE = Decimal("0.20")
```

## Taux applicable

TVA France : **20%** sur les panneaux de signalisation (bien meuble ordinaire, pas d'exonération).

## Fichiers concernés

- `catalog/api/serializers.py` — `ProductVariantSerializer`, `ProductListSerializer`
- `orders/api/serializers.py` — `OrderLineSerializer`, `OrderSerializer` (pour les totaux TTC)
- `orders/domain/rules.py` — `compute_shipping_fee()` : vérifier si frais de port sont HT ou TTC
- `signals/settings/base.py` — constante `VAT_RATE = Decimal("0.20")`

## Acceptance criteria

- `GET /api/products/` expose `price_ht` et `price_ttc` sur chaque variant
- `GET /api/orders/mine/` expose `subtotal_ttc` et `total_ttc`
- Le taux TVA est centralisé dans les settings (pas hardcodé dans les sérialiseurs)
- Les montants dans Stripe Checkout correspondent bien au TTC (Stripe prend des montants en centimes)
