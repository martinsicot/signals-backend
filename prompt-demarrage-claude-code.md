# Prompt de démarrage — Claude Code

Copie-colle ce prompt dans Claude Code pour démarrer le projet. Il contient tout le contexte nécessaire pour qu'il parte sur de bonnes bases sans avoir à ré-expliquer l'historique.

---

## PROMPT À COPIER

```
Je démarre un projet Django/DRF pour un site e-commerce B2C. Le but de cette
première session est de poser le socle technique et la structure, sans
connaissance produit spécifique (le catalogue réel sera branché plus tard,
sur une verticale "panneaux de signalisation" — mais rien dans ce socle ne
doit être spécifique à ce métier).

## Stack

- Django + Django REST Framework
- PostgreSQL
- Redis + Celery (prévu pour plus tard, pas de tâches Celery à écrire maintenant,
  juste que la config soit prête)
- Pytest pour les tests (pas unittest / TestCase Django natif)
- Docker + docker-compose pour le dev local

## Architecture : Domain / Service / Data

Je veux une architecture en couches, inspirée du Django Styleguide (HackSoft) :

- **domain/** : logique métier pure, aucune dépendance Django. Dataclasses
  Python pour les entités métier (ex: Order, OrderLine), fonctions de règles
  métier (validation, calculs), exceptions métier custom.
- **models.py** : uniquement l'ORM Django. Pas de logique métier dedans.
  Juste de la persistance.
- **repositories/** : traduisent entre l'ORM (models.py) et les entités
  domain. Seule couche qui a le droit de faire des requêtes ORM directes
  en dehors de l'admin Django.
- **services/** : orchestrent domain + repositories. Gèrent les transactions,
  déclenchent les side-effects (emails, tâches Celery). C'est la seule
  couche appelée par les vues/API.
- **api/** : vues DRF (serializers, views, urls). Ne contiennent AUCUNE
  logique métier — elles appellent uniquement les services, gèrent
  sérialisation et codes HTTP.

Règle stricte : les vues ne touchent JAMAIS directement à l'ORM. Seuls les
repositories ont le droit d'importer et utiliser les models Django.

Structure de dossiers par app :
app_name/
├── models.py
├── domain/
│   ├── entities.py
│   ├── rules.py
│   └── exceptions.py
├── services/
│   └── xxx_service.py
├── repositories/
│   └── xxx_repository.py
├── api/
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
└── tests/
    ├── test_domain.py
    ├── test_services.py
    └── test_api.py

Applique cette architecture UNIQUEMENT là où il y a une vraie logique
métier (calculs, validations, règles). Pour du CRUD pur sans règle
métier propre, un repository simple suffit — ne crée pas de couche
domain artificielle juste pour respecter le pattern.

## Apps à créer dans cette session

1. **accounts** — Customer (particulier), pas de logique métier complexe,
   auth Django standard (pas besoin de domain layer poussé ici).
2. **catalog** — Product, Category. Générique, sans notion de "panneau"
   ni d'attributs spécifiques à un métier. CRUD via repository simple,
   pas de domain layer complexe (pas de règle métier propre à ce stade).
3. **orders** — Order, OrderLine. Ici il y a une vraie logique métier :
   - calcul du total (subtotal + frais de port)
   - règle de frais de port (ex: gratuit au-dessus d'un seuil configurable)
   - validation d'une commande (ex: pas de commande vide, quantité max
     avant redirection vers un parcours "devis" — prévoir l'entité mais
     sans implémenter le parcours devis, hors scope)
   - statuts de commande (pending, paid, in_production, shipped) en Enum

Ne crée PAS encore de vues DRF complexes pour le paiement (Stripe) —
seulement la structure des modèles/domain/services pour create_order()
et un endpoint API minimal pour créer une commande, sans intégration
paiement réelle pour l'instant.

## Conventions de tests — IMPORTANT, à respecter strictement

- Utiliser **pytest** (pas de `TestCase` Django natif), avec `pytest-django`.
- Organiser les tests dans des classes : `class TestSomethingToTest:`
  (le nom de la classe décrit ce qui est testé, pas "TestOrder" mais
  par exemple `TestOrderCreation`, `TestShippingFeeCalculation`).
- Chaque méthode de test commence par `test_` et décrit le comportement
  attendu de façon lisible, au format :
  `test_<subject>_<expected_result>_when_<condition>`
  Exemples :
  - `test_api_returns_ok_when_order_is_valid`
  - `test_api_returns_422_when_order_exceeds_max_quantity`
  - `test_shipping_fee_is_zero_when_subtotal_above_threshold`
  - `test_create_order_raises_error_when_cart_is_empty`
- Structurer CHAQUE test avec la méthode **AAA (Arrange, Act, Assert)**,
  avec des commentaires ou un espacement clair séparant les 3 blocs :

  def test_shipping_fee_is_zero_when_subtotal_above_threshold(self):
      # Arrange
      subtotal = Decimal("250.00")

      # Act
      fee = compute_shipping_fee(subtotal)

      # Assert
      assert fee == Decimal("0")

- Priorité de couverture (dans cet ordre) :
  1. Règles métier du domain layer (rules.py) — tests rapides, sans DB,
     couverture maximale car c'est le cœur de la valeur.
  2. Services — tests avec DB (ou repository mocké selon pertinence),
     couvrir les cas nominaux + cas d'erreur métier (exceptions).
  3. API — tests d'intégration sur les parcours critiques uniquement
     (création commande valide, rejet commande invalide, codes HTTP
     corrects). Pas besoin de tester l'exhaustivité des validations
     de serializer si elles sont déjà couvertes au niveau service/domain.
- On veut de la couverture PERTINENTE, pas de la couverture pour la
  métrique : ne génère pas de tests triviaux qui ne testent aucune
  logique réelle (ex: pas besoin de tester qu'un champ CharField accepte
  une string). Priorise les règles métier, les cas limites, et les
  chemins d'erreur.
- Utilise `pytest.mark.django_db` uniquement sur les tests qui touchent
  réellement la DB (services, API), jamais sur les tests domain purs.
- Utilise des fixtures pytest (`conftest.py`) pour les objets de test
  réutilisables (customer de test, produit de test), pas de factories
  complexes (factory_boy) pour l'instant sauf si tu juges que ça
  simplifie vraiment la lisibilité.

## Ce qui est HORS SCOPE pour cette session

- Configurateur de panneau (n'existe pas dans ce socle générique)
- Intégration Stripe réelle (webhooks, paiement)
- Parcours devis / collectivités
- Tâches Celery concrètes (juste la config de base doit être prête)
- Django Admin poussé (juste l'enregistrement basique des modèles)
- Frontend (htmx/templates) — uniquement l'API DRF pour cette session

## Livrable attendu

- Structure de projet Django complète et fonctionnelle (settings dev/prod
  séparés, docker-compose local avec Postgres + Redis)
- Apps accounts / catalog / orders avec l'architecture domain/service/data
  décrite ci-dessus
- Tests pytest respectant les conventions ci-dessus, avec une couverture
  centrée sur la logique métier réelle
- Un README court expliquant comment lancer le projet en local
  (docker-compose up, migrations, run tests)

Commence par me proposer la structure de dossiers et les settings de base,
je valide avant que tu génères le reste.
```

---

## Pourquoi ce prompt est structuré ainsi

- **Contexte complet en une fois** : Claude Code n'a pas accès à notre conversation ici, donc tout ce qui compte (stack, architecture, scope, conventions de tests) doit être explicite dès le départ.
- **"Commence par me proposer la structure... je valide"** : évite qu'il génère 30 fichiers d'un coup dans une direction que tu n'approuves pas — tu gardes la main sur les décisions structurantes avant qu'il ne code en volume.
- **Conventions de tests explicites avec exemples concrets** : Claude Code suit très bien les conventions quand elles sont données avec un exemple de code exact (le AAA avec commentaires), plutôt qu'une description abstraite.
- **Hors scope explicite** : évite qu'il parte sur des tangentes (Stripe, Celery tasks) qui gonfleraient la session pour rien.

## Suggestion pour la suite

Une fois que Claude Code a généré le socle, tu peux lui donner mon fichier `architecture-domain-service-data.md` en complément si tu veux qu'il garde les exemples de code qu'on a définis ensemble comme référence stylistique exacte.
