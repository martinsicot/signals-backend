# BUG-003 — Délai fabrication absent des sérialiseurs variant

## Statut
DONE ✅

## Priorité
🔴 BLOQUANT (requis pour T5.6 backlog)

## Problème

Le modèle `PriceCell` a un champ `delai` (délai de fabrication en jours), et `PriceScheduleSize` a également des données de délai. Ces informations sont **absentes** de `ProductVariantSerializer` et `ProductVariantDetailSerializer`.

Le frontend ne peut donc pas afficher le délai de fabrication avant le passage en paiement (T5.6 du backlog : "Validation des stocks/délais avant passage en paiement — affichage délai fabrication 3j").

## Comportement actuel

`GET /api/variants/42/` retourne :
```json
{
  "id": 42,
  "sku": "...",
  "price": "129.00",
  "weight_kg": "2.5",
  "is_active": true,
  "attributes": [...]
}
```
→ Pas de `delai`.

## Solution attendue

Ajouter `delai` dans `ProductVariantDetailSerializer` (et optionnellement dans `ProductVariantSerializer` pour la liste) :

```python
class ProductVariantDetailSerializer(serializers.ModelSerializer):
    delai = serializers.IntegerField(source="price_cell.delai", read_only=True)
    # ...
```

## Fichiers concernés

- `catalog/api/serializers.py` — `ProductVariantSerializer`, `ProductVariantDetailSerializer`
- `catalog/models.py` — vérifier la relation `ProductVariant → price_cell → delai`

## Acceptance criteria

- `GET /api/variants/<id>/` inclut un champ `delai` (entier, nombre de jours)
- `GET /api/products/<slug>/` via `ProductDetailSerializer` expose `delai` sur chaque variant
- Si `price_cell` est null, `delai` vaut `null`
