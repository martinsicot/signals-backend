# TEST-008 — Test E2E tunnel panier → paiement → confirmation (T8.2 backlog)

## Priorité
🟡 IMPORTANT

## Contexte

T8.2 du backlog : "Tests parcours complet panier → paiement → confirmation" est non coché.

Également T6.6 : "Tests en mode Stripe test (carte test, webhook local avec Stripe CLI)".

## Tests à écrire

### Parcours invité complet

1. Ajouter un produit au panier (`POST /api/cart/add/`)
2. Créer une commande (`POST /api/orders/` avec `guest_email`)
3. Lancer le checkout (`POST /api/orders/<id>/checkout/`)
4. Simuler le webhook Stripe (`checkout.session.completed`)
5. Vérifier que la commande est en `paid`
6. Vérifier que l'email de confirmation a été envoyé

### Parcours utilisateur connecté

1. S'inscrire et se connecter
2. Ajouter au panier
3. Créer commande avec adresse sauvegardée
4. Lancer checkout
5. Simuler webhook
6. Vérifier statut + email + PDF facture

### Validation des règles métier

7. Commande > 50 articles → rejetée
8. Commande avec variant inactif → rejetée
9. Frais de port à 0 si total > 200€
10. Frais de port à 9.90€ si total ≤ 200€

## Outil recommandé

Utiliser `stripe listen --forward-to localhost:8000/api/webhooks/stripe/` en dev pour tester les webhooks réels.

## Fichiers concernés

- `tests/orders/test_e2e.py` (à créer)
- `tests/conftest.py` — fixtures produits/variants

## Acceptance criteria

- Le parcours invité complet est couvert par des tests automatisés
- Le parcours connecté est couvert
- Les règles métier (frais de port, quantité max) sont testées en intégration
