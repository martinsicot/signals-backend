# Architecture Domain / Service / Data — Django

## Principe général

L'idée : **découpler la logique métier du framework Django** (ORM, requêtes HTTP, admin). Django devient un détail d'implémentation (persistance + delivery), pas le centre du projet. C'est proche du pattern popularisé par le "Django Styleguide" (HackSoft), qui a fait ses preuves sur des projets e-commerce/B2B comme le tien.

**3 couches, dépendance dans un seul sens :**

```
views/API (DRF)  →  Service  →  Domain
                        ↓
                      Data (ORM / repositories)
```

- **Domain** : les règles métier pures. Aucune dépendance Django. Ce sont des objets Python simples (dataclasses) + fonctions/règles.
- **Service** : orchestre. Appelle le domain, appelle la data layer, gère les transactions, déclenche les side-effects (email, Celery). C'est la seule couche qui a le droit d'écrire.
- **Data** : les modèles Django (ORM) + repositories qui traduisent entre ORM et objets domain.

La règle d'or : **les vues/API ne parlent jamais directement à l'ORM**. Elles appellent des services. Les services orchestrent domain + repositories.

---

## Structure de dossiers par app Django

```
orders/
├── models.py              # ORM only — pas de logique métier ici
├── domain/
│   ├── entities.py         # Order, OrderLine (dataclasses, pas de Django)
│   ├── rules.py             # calcul de prix, règles de validation métier
│   └── exceptions.py        # OrderInvalidError, InsufficientStockError...
├── services/
│   ├── order_service.py     # create_order(), validate_order(), mark_as_paid()
│   └── pricing_service.py   # compute_total(), apply_shipping_fee()
├── repositories/
│   └── order_repository.py  # OrderRepository — traduit ORM <-> domain entities
├── api/
│   ├── serializers.py
│   ├── views.py              # appelle services uniquement
│   └── urls.py
└── tests/
    ├── test_domain.py        # tests purs Python, ultra rapides, pas de DB
    ├── test_services.py      # tests avec DB (ou repo mocké)
    └── test_api.py           # tests d'intégration end-to-end
```

---

## Exemple concret sur ton projet : passer une commande

### 1. Domain (`orders/domain/entities.py`)

Pas de Django ici. Juste des objets métier et des règles.

```python
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    IN_PRODUCTION = "in_production"
    SHIPPED = "shipped"

@dataclass
class OrderLine:
    product_id: int
    quantity: int
    unit_price: Decimal

    @property
    def total(self) -> Decimal:
        return self.unit_price * self.quantity

@dataclass
class Order:
    id: int | None
    customer_id: int
    lines: list[OrderLine]
    status: OrderStatus
    shipping_fee: Decimal

    @property
    def subtotal(self) -> Decimal:
        return sum((line.total for line in self.lines), Decimal("0"))

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.shipping_fee
```

### 2. Règles métier (`orders/domain/rules.py`)

```python
from decimal import Decimal
from .entities import Order
from .exceptions import EmptyOrderError, OrderTooLargeError

MAX_PANELS_PARTICULIER = 50  # règle métier : au-delà, on redirige vers devis pro

def validate_order_for_particulier(order: Order) -> None:
    if not order.lines:
        raise EmptyOrderError()

    total_qty = sum(line.quantity for line in order.lines)
    if total_qty > MAX_PANELS_PARTICULIER:
        raise OrderTooLargeError(
            f"Commande de {total_qty} panneaux : redirection vers devis pro requise"
        )

def compute_shipping_fee(subtotal: Decimal) -> Decimal:
    # règle métier pure, testable sans DB
    if subtotal >= Decimal("200"):
        return Decimal("0")
    return Decimal("9.90")
```

**Pourquoi c'est puissant** : `test_domain.py` teste `validate_order_for_particulier()` sans base de données, sans Django, en quelques millisecondes. Tu peux avoir 200 tests domain qui tournent en moins d'une seconde.

### 3. Data — Modèles ORM (`orders/models.py`)

Les modèles restent "bêtes" : juste de la persistance, pas de logique métier dedans.

```python
from django.db import models

class OrderModel(models.Model):
    customer = models.ForeignKey("accounts.Customer", on_delete=models.PROTECT)
    status = models.CharField(max_length=20, default="pending")
    shipping_fee = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class OrderLineModel(models.Model):
    order = models.ForeignKey(OrderModel, related_name="lines", on_delete=models.CASCADE)
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
```

### 4. Data — Repository (`orders/repositories/order_repository.py`)

Le repository traduit entre ORM et entités domain. C'est le SEUL endroit qui touche à `OrderModel`.

```python
from django.db import transaction
from ..domain.entities import Order, OrderLine, OrderStatus
from ..models import OrderModel, OrderLineModel

class OrderRepository:
    def save(self, order: Order) -> Order:
        with transaction.atomic():
            order_model = OrderModel.objects.create(
                customer_id=order.customer_id,
                status=order.status.value,
                shipping_fee=order.shipping_fee,
            )
            OrderLineModel.objects.bulk_create([
                OrderLineModel(
                    order=order_model,
                    product_id=line.product_id,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                )
                for line in order.lines
            ])
        order.id = order_model.id
        return order

    def get_by_id(self, order_id: int) -> Order:
        order_model = OrderModel.objects.prefetch_related("lines").get(id=order_id)
        return self._to_entity(order_model)

    def _to_entity(self, model: OrderModel) -> Order:
        return Order(
            id=model.id,
            customer_id=model.customer_id,
            status=OrderStatus(model.status),
            shipping_fee=model.shipping_fee,
            lines=[
                OrderLine(product_id=l.product_id, quantity=l.quantity, unit_price=l.unit_price)
                for l in model.lines.all()
            ],
        )
```

### 5. Service (`orders/services/order_service.py`)

C'est ici que tout s'orchestre : domain + repository + side-effects (email, Celery).

```python
from decimal import Decimal
from ..domain.entities import Order, OrderLine, OrderStatus
from ..domain.rules import validate_order_for_particulier, compute_shipping_fee
from ..repositories.order_repository import OrderRepository
from catalog.repositories.product_repository import ProductRepository
from notifications.tasks import send_order_confirmation_email

class OrderService:
    def __init__(self):
        self.order_repo = OrderRepository()
        self.product_repo = ProductRepository()

    def create_order(self, customer_id: int, cart_items: list[dict]) -> Order:
        lines = [
            OrderLine(
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price=self.product_repo.get_price(item["product_id"]),
            )
            for item in cart_items
        ]

        subtotal = sum((l.total for l in lines), Decimal("0"))
        shipping_fee = compute_shipping_fee(subtotal)

        order = Order(
            id=None,
            customer_id=customer_id,
            lines=lines,
            status=OrderStatus.PENDING,
            shipping_fee=shipping_fee,
        )

        validate_order_for_particulier(order)  # peut lever une exception métier

        order = self.order_repo.save(order)
        send_order_confirmation_email.delay(order.id)  # Celery, async

        return order
```

### 6. API / Vue (`orders/api/views.py`)

La vue ne fait QUE : parser la requête, appeler le service, sérialiser la réponse. Zéro logique métier.

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from ..services.order_service import OrderService
from ..domain.exceptions import OrderTooLargeError, EmptyOrderError

class CreateOrderView(APIView):
    def post(self, request):
        service = OrderService()
        try:
            order = service.create_order(
                customer_id=request.user.customer.id,
                cart_items=request.data["items"],
            )
        except OrderTooLargeError as e:
            return Response({"error": str(e), "redirect": "devis"}, status=422)
        except EmptyOrderError:
            return Response({"error": "Panier vide"}, status=400)

        return Response({"order_id": order.id, "total": str(order.total)}, status=201)
```

---

## Pourquoi ce pattern est particulièrement pertinent pour toi

1. **Réutilisabilité multi-vertical** : la couche `domain` (règles de calcul de prix, validation de commande) ne dépend pas de Django. Si tu dupliques le modèle sur un 3ᵉ vertical, tu peux littéralement copier-coller ou packager la logique domain commune (ex. un package interne `ecommerce_core`).

2. **Tests ultra-rapides** : tes règles métier (seuil particulier/pro, calcul frais de port, validation devis) se testent sans base de données. Sur un side-project où tu codes par sessions courtes, pouvoir lancer 300 tests en 2 secondes plutôt qu'en 30 secondes change vraiment le confort de dev.

3. **Le jour où le devis collectivités arrive (V2)** : tu ajoutes juste un nouveau service `QuoteService` et de nouvelles règles domain (`validate_quote_for_collectivite`), sans toucher à `OrderService`. La séparation limite les régressions.

4. **Django Admin reste intact** : l'admin continue de taper directement sur les `Model` (c'est un outil interne, pas besoin de le faire passer par les services). Tu gardes donc toute la vélocité de l'admin Django pour la gestion catalogue, sans compromis architectural.

---

## Point d'équilibre — ne pas sur-ingénierer

Pour une V1 avec un scope volontairement resserré (vu la conversation précédente), je te conseille de **n'appliquer ce pattern qu'aux zones à forte valeur métier** :

- ✅ `orders/` (commande, calcul prix, validation) — logique métier réelle, ça vaut le coup.
- ✅ `pricing/` si tu extrais le calcul de prix (utile pour préparer le futur configurateur).
- ⚠️ `catalog/` — probablement juste du CRUD, pas besoin de domain layer complexe. Un repository simple suffit, pas la peine de créer des entités domain pour un `Product` qui n'a pas de règles métier propres.
- ❌ `accounts/` (auth) — reste sur Django/DRF standard, ne réinvente pas l'authentification avec ce pattern, aucun bénéfice.

La règle pratique : **si un objet a des règles de calcul ou de validation non triviales, il mérite une couche domain. S'il n'est que du stockage/affichage, une repository simple suffit.**

---

## Convention de nommage pour rester cohérent

| Couche | Convention | Exemple |
|---|---|---|
| Domain entity | `Order`, `Product` (nom métier pur) | `orders/domain/entities.py` |
| ORM model | `OrderModel`, `ProductModel` (suffixe explicite) | `orders/models.py` |
| Repository | `XRepository` avec `save()`, `get_by_id()`, `list()` | `OrderRepository` |
| Service | `XService` avec des méthodes verbe+nom (`create_order`, `mark_as_paid`) | `OrderService` |
| Exception métier | `XError` héritant d'une base `DomainError` | `OrderTooLargeError` |
