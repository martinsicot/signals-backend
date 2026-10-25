# FEAT-006 — Recherche produit (T4.4 backlog)

## Priorité
🟡 IMPORTANT

## Contexte

T4.4 du backlog est non coché. L'endpoint `GET /api/products/?q=...` existe dans `ProductListView` mais son implémentation est à valider/tester.

## Ce qu'il faut vérifier

1. Le paramètre `q` est-il effectivement appliqué dans `ProductListView` ?
2. Quels champs sont searchés (name ? description ? base_code ?)
3. Est-ce un `icontains` simple ou un search plus avancé ?
4. Les résultats sont-ils pertinents pour les cas d'usage réels (ex: "stop", "cédez le passage", "B1") ?

## Améliorations attendues

Si la recherche basique `icontains` est insuffisante :

- Rechercher sur `Product.name`, `Product.description`, `Product.base_code`, `Category.name`
- Chercher aussi dans les slugs pour compatibilité avec les codes réglementaires (ex: "AB3a")
- Retourner les catégories qui matchent (pour navigation)

## Fichiers concernés

- `catalog/api/views.py` — `ProductListView` : vérifier le filtre `q`
- `catalog/repositories/product_repository.py` — requête de filtrage

## Acceptance criteria

- `GET /api/products/?q=stop` retourne les produits dont le nom contient "stop"
- `GET /api/products/?q=B1` retourne les produits avec le code réglementaire B1
- La recherche est insensible à la casse
- Combinable avec les autres filtres (`?q=stop&shape=rond`)
