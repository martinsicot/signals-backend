# INFRA-010 — Bascule Stripe mode live + validation prod (T9.1, T9.4, T9.5 backlog)

## Priorité
🟡 IMPORTANT (requis avant ouverture au public)

## Tâches

### T9.1 — Passer Stripe en mode live

1. Aller sur dashboard.stripe.com → activer le compte (compléter KYB si nécessaire)
2. Récupérer les clés live : `pk_live_...` et `sk_live_...`
3. Créer le webhook live pointant vers `https://api.signals.fr/api/webhooks/stripe/`
   - Event : `checkout.session.completed`, `checkout.session.expired`, `payment_intent.payment_failed`
4. Récupérer le `whsec_...` du webhook live
5. Mettre à jour les variables d'env en prod dans Coolify

### T9.4 — Vérifications finales

- [ ] SSL actif sur le domaine API
- [ ] SSL actif sur le domaine frontend
- [ ] Emails transactionnels reçus (test via Brevo)
- [ ] Webhook Stripe reçu et traité (test avec Stripe Dashboard → "Envoyer un event test")
- [ ] Logs d'erreur propres (pas de 500 sur les routes principales)
- [ ] Django Admin accessible et fonctionnel

### T9.5 — Commande de test réelle

- Effectuer une vraie commande avec une vraie CB (petit montant possible : variant le moins cher)
- Vérifier :
  - [ ] Redirection vers Stripe Checkout
  - [ ] Paiement accepté
  - [ ] Redirection vers page de confirmation frontend
  - [ ] Email de confirmation reçu
  - [ ] Facture PDF jointe à l'email
  - [ ] Commande visible dans Django Admin avec statut `paid`
  - [ ] Notification admin reçue

## Acceptance criteria

- La commande de test T9.5 se déroule sans erreur
- L'argent apparaît dans le tableau de bord Stripe
- Rembourser la commande test depuis Stripe Dashboard
