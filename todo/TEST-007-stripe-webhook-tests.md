# TEST-007 — Tests Stripe webhook (T8.3 backlog)

## Priorité
🟡 IMPORTANT

## Contexte

T8.3 du backlog : "Tests webhook Stripe (cas succès + échec)" est non coché.

Le webhook est le point critique du tunnel de paiement — c'est lui qui marque la commande comme PAID et envoie la facture. Un bug ici = commandes payées mais non confirmées.

## Tests à écrire

### Cas nominaux

1. **`checkout.session.completed`** → commande passe en `paid`, email envoyé
   - Mock : `stripe.Webhook.construct_event` retourne l'event
   - Vérifier : `order.status == "paid"`, task `send_payment_confirmation` appelée

2. **`checkout.session.expired`** → commande passe en `cancelled`

3. **`payment_intent.payment_failed`** → commande passe en `cancelled`

### Cas d'erreur

4. **Signature invalide** → 400, rien ne se passe en base
5. **Event inconnu** → 200 (ignore silencieusement)
6. **Commande introuvable** → 404 ou log d'erreur, pas de crash

### Cas limites

7. **Webhook reçu deux fois** (retry Stripe) → idempotence : ne pas doubler les emails
8. **Commande déjà en `paid`** → ne pas re-déclencher les notifications

## Fichiers concernés

- `tests/orders/test_webhook.py` (à créer)
- `orders/api/payment_views.py` — `StripeWebhookView`
- `orders/services/payment_service.py` — `handle_webhook()`

## Commande

```bash
pytest tests/orders/test_webhook.py -v
```

## Acceptance criteria

- Tous les cas ci-dessus ont un test
- Les tests mockent Stripe (pas d'appel réseau réel)
- Coverage de `payment_views.py` et `payment_service.py` ≥ 90%
