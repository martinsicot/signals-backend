# Budget infrastructure & finances

## Infrastructure — montée en charge progressive

### Phase 1 — Lancement (0 à 6 mois) — ~230–530 €/mois

| Poste | Solution | Coût |
|---|---|---|
| Backend Django + PostgreSQL | Railway Starter | ~5 €/mois |
| Frontend React | Vercel | Gratuit |
| Fichiers & médias | Cloudflare R2 | Gratuit < 10 Go |
| Emails transactionnels | Brevo | Gratuit (300 emails/jour) |
| Domaine | Namecheap / OVH | ~10 €/an |
| Paiement | Stripe | 0 € fixe + 1,4 % + 0,25 € / transaction UE |
| **Google Ads (SEA)** | Google | ~200–500 €/mois |
| **Backlinks** | Annuaires pro, liens sponsorisés | ~0 €/mois (mois 2–3 : 200–300 €) |

**Total fixe estimé : ~230–530 €/mois** (hors commission Stripe)

> Le SEA est indispensable au lancement pour générer du trafic pendant que le SEO monte naturellement (6 à 12 mois minimum).

### Phase 2 — Croissance (6 à 18 mois) — ~300–700 €/mois

| Service | Solution | Coût estimé |
|---|---|---|
| Serveur Django | VPS Hetzner | ~10–20 €/mois |
| PostgreSQL managé | Supabase / Railway Pro | ~15–25 €/mois |
| Fichiers & médias | Cloudflare R2 | Selon volume |
| CDN | Cloudflare (gratuit) | 0 € |
| Monitoring | Sentry (free tier) | 0 € |
| Google Ads | Google | ~200–500 €/mois |
| Backlinks | Liens sponsorisés ciblés | ~200–300 €/mois |

**Total fixe estimé : ~300–700 €/mois**

### Phase 3 — Scale (18 mois+) — ~150–300 €/mois

| Service | Solution | Coût estimé |
|---|---|---|
| Conteneurs | Railway Pro / Fly.io | ~50–100 €/mois |
| PostgreSQL répliqué | Managé | ~30–60 €/mois |
| CDN assets | Cloudflare / Bunny.net | ~10–20 €/mois |
| Monitoring | Sentry Pro | ~20 €/mois |

**Total fixe estimé : ~150–300 €/mois**

---

## Questions financières à clarifier

### Société
- [ ] Quel capital de départ ?
- [ ] Répartition des parts (50/50 ou autre)
- [ ] Qui met de l'argent au départ et combien ?
- [ ] Salaires ou dividendes ?

### Prix & marges
- [ ] Prix d'achat unitaire au fabricant tchèque par gamme
- [ ] Frais de port entrants (RTC → client final)
- [ ] Marge brute cible (référence e-commerce physique : 40–60 %)
- [ ] Gestion des fluctuations de prix côté fabricant

### Livraison côté client
- [ ] Frais de port inclus dans le prix ou facturés en sus ?
- [ ] Seuil de livraison gratuite ?
- [ ] Qui absorbe le coût si colis perdu ou endommagé ?

### TVA & fiscalité
- [ ] Assujettissement TVA dès le départ (probablement oui en SAS/SARL)
- [ ] Achats en RTC = TVA intracommunautaire → mécanisme d'autoliquidation à valider avec un comptable
- [ ] Collectivités = exonération TVA → factures et bons de commande adaptés

### Coûts marketing (gérés en interne)
- Google Ads au lancement : **200–500 €/mois**
- Backlinks à partir du mois 2–3 : **200–300 €/mois**
- Prestation SEO freelance ponctuelle (audit + stratégie mots-clés) : **500–1 000 € une fois**

---

## Seuil de rentabilité — estimation indicative

```
Coûts fixes mensuels estimés :
  Infra technique          ~15–80 €
  Google Ads               ~200–500 €
  Backlinks                ~200–300 € (à partir du mois 2–3)
  Comptable                ~100–200 €
  Charges société          selon statut
─────────────────────────────────────────
Total fixe estimé          ~500–1 100 €/mois

→ À croiser avec : panier moyen x marge brute
→ Combien de commandes/mois pour atteindre l'équilibre ?
```

**Première action concrète** : obtenir les prix d'achat réels au fabricant tchèque et les prix du marché français pour valider la marge et la compétitivité.
