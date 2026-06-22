# Architecture technique

## Stack

| Couche | Technologie | Remarque |
|---|---|---|
| Backend | Django + DRF | API REST, admin catalogue, webhooks Stripe |
| Frontend | React | Configurateur, catalogue, tunnel paiement |
| Base de données | PostgreSQL | Natif Django, robuste |
| Paiement | Stripe | CB, Apple/Google Pay, SEPA, TVA auto (Stripe Tax) |
| Fichiers & médias | Cloudflare R2 | Compatible S3, très peu cher |
| Emails transactionnels | Brevo | Free tier 300 emails/jour |

## Architecture globale

```
React (Frontend)
      ↕ API REST
Django + DRF (Backend)
      ↕
PostgreSQL (BDD)
      ↕
Stripe (Paiement)
      ↕
Génération fichier technique (SVG/PDF)
      ↕
Envoi automatique au fabricant (email / API)
```

## Modèle de données (schéma simplifié)

```python
Country
└── Category
    └── Product (type: fixe / configurable / sur_devis)
        ├── ProductVariant (taille, matériau, classe réfléchissante…)
        └── ConfigurableField (texte libre, blason, options visuelles…)
```

## Ce que l'IA fait pour le front

Avec Cursor ou Claude :
- Génération des composants React du configurateur
- Prévisualisation SVG en temps réel
- Pages catalogue et fiches produits
- Intégration Stripe Elements côté client
- Gestion du responsive et de l'internationalisation

## Ce qu'on anticipe sans développer maintenant

- URLs localisées dès le départ (`/fr/`, `/es/`…) même si seule la France est active
- Structure i18n en place côté React et Django
- Architecture catalogue multi-pays (un catalogue par pays)
- Stripe configuré pour les paiements européens et la TVA intracommunautaire (OSS)

## Ce qu'on évite

- **Shopify / WooCommerce** → perte de contrôle sur la logique métier spécifique (configurateur, envoi auto fournisseur, multi-pays)
- **Trop de React dès le départ** → pages Django classiques là où ce n'est pas nécessaire, React uniquement pour le configurateur et le catalogue

## Django Admin

Suffisant pour gérer le catalogue au départ.  
L'associé pourra ajouter/modifier des produits sans toucher au code.
