# Structure du site & catalogue

## Pages principales

- Accueil
- Catalogue (avec filtres : catégorie, usage, format, matériau)
- Fiche produit
- Configurateur (panneaux personnalisables)
- Panier / Commande / Paiement (Stripe)
- Espace client (suivi de commande)
- Pages institutionnelles (À propos, CGV, Contact, FAQ)

## Organisation du catalogue

L'organisation se fait **par pays**, pas par produit avec déclinaisons :

```
Pays (France, Espagne, Allemagne…)
└── Catalogue spécifique au pays
    └── Catégorie (danger, obligation, information, ville…)
        └── Panneau
            ├── Variantes fixes (taille, matériau, classe réfléchissante)
            ├── Champs configurables (texte libre, blason, options visuelles…)
            └── Prix
```

Chaque pays a sa propre réglementation → ses propres panneaux.  
Un panneau "stop" français et un panneau "stop" espagnol sont deux produits différents, pas des variantes.

## Les 3 types de produits

### Type 1 — Produit fixe avec variantes
*(ex : panneau de danger, stop, cédez le passage)*
- Référence unique avec options prédéfinies
- Variantes connues : taille S/M/L, matériau, classe réfléchissante
- Pas de saisie libre → simple sélection

### Type 2 — Produit configurable
*(ex : panneau de nom de ville, panneau de rue)*
- Champs de saisie libre (nom de la ville, population, blason…)
- Prévisualisation en temps réel → argument de vente fort
- Prix potentiellement variable selon le contenu

### Type 3 — Produit sur devis
*(demandes très spécifiques ou grandes quantités)*
- Formulaire de contact dédié
- Non prioritaire au lancement, mais à anticiper

## Le configurateur — pièce centrale

Pour les panneaux de nom de ville notamment, un configurateur visuel avec prévisualisation SVG en temps réel est quasi-indispensable.

Approche technique recommandée :
- **SVG dynamique** côté client pour la prévisualisation (léger, rapide, vectoriel)
- Génération d'un fichier propre côté serveur (SVG/PDF) au moment de la commande pour transmission au fabricant

## Stratégie géographique

- **Lancement** : France uniquement (seul catalogue maîtrisé côté produit)
- **Architecture anticipée** dès maintenant pour l'Europe : ajout d'un pays = ajout d'un catalogue, sans toucher au reste
- URLs localisées dès le départ (`/fr/`, `/es/`, `/de/`…)
- Langue, devise et TVA s'adaptent automatiquement au pays choisi
- SEO isolé par pays

## Flux commande automatisé

```
Paiement Stripe validé
        ↓
Webhook Django déclenché
        ↓
Génération automatique du fichier technique (SVG/PDF)
        ↓
Envoi automatique au fabricant tchèque
        ↓
Email de confirmation envoyé au client
```
