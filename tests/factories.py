import factory
from django.contrib.auth.models import Group
from factory.django import DjangoModelFactory

from accounts.models import Address, Customer, User
from catalog.models import (
    Attribute,
    AttributeValue,
    Category,
    Product,
    ProductVariant,
    ProductVariantAttribute,
)
from orders.models import OrderLineModel, OrderModel


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ("name",)

    name = factory.Iterator(["customer", "crm", "ops"])


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name", locale="fr_FR")
    last_name = factory.Faker("last_name", locale="fr_FR")
    password = factory.PostGenerationMethodCall("set_password", "testpassword123")
    is_active = True
    is_staff = False


class CustomerUserFactory(UserFactory):
    """A User that belongs to the 'customer' group and has a Customer profile."""

    @factory.post_generation
    def add_to_customer_group(self, create, extracted, **kwargs):
        if not create:
            return
        group, _ = Group.objects.get_or_create(name="customer")
        self.groups.add(group)


def _add_user_to_group(user, group_name):
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)


class StaffUserFactory(UserFactory):
    """A User that belongs to 'crm' or 'ops' — no Customer profile.

    Concrete subclasses assign the group via their own ``add_to_group`` hook.
    """

    is_staff = True
    email = factory.Sequence(lambda n: f"staff{n}@example.com")


class CRMUserFactory(StaffUserFactory):
    email = factory.Sequence(lambda n: f"crm{n}@example.com")

    @factory.post_generation
    def add_to_group(self, create, extracted, **kwargs):
        if create:
            _add_user_to_group(self, "crm")


class OpsUserFactory(StaffUserFactory):
    email = factory.Sequence(lambda n: f"ops{n}@example.com")

    @factory.post_generation
    def add_to_group(self, create, extracted, **kwargs):
        if create:
            _add_user_to_group(self, "ops")


class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = Customer

    user = factory.SubFactory(CustomerUserFactory)
    phone = factory.Faker("phone_number", locale="fr_FR")


class AddressFactory(DjangoModelFactory):
    class Meta:
        model = Address

    customer = factory.SubFactory(CustomerFactory)
    first_name = factory.Faker("first_name", locale="fr_FR")
    last_name = factory.Faker("last_name", locale="fr_FR")
    company = ""
    line1 = factory.Faker("street_address", locale="fr_FR")
    line2 = ""
    city = factory.Faker("city", locale="fr_FR")
    postal_code = factory.Faker("postcode", locale="fr_FR")
    country = "FR"
    is_default = False


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")
    description = ""


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product
        django_get_or_create = ("slug",)

    category = factory.SubFactory(CategoryFactory)
    base_code = factory.Sequence(lambda n: f"TEST-{n}")
    name = factory.Sequence(lambda n: f"Product {n}")
    slug = factory.Sequence(lambda n: f"product-{n}")
    type = "Panneau"
    is_active = True


class AttributeFactory(DjangoModelFactory):
    class Meta:
        model = Attribute
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Attribute {n}")
    slug = factory.Sequence(lambda n: f"attribute-{n}")


class AttributeValueFactory(DjangoModelFactory):
    class Meta:
        model = AttributeValue
        django_get_or_create = ("attribute", "value")

    attribute = factory.SubFactory(AttributeFactory)
    value = factory.Sequence(lambda n: f"value-{n}")
    display = factory.LazyAttribute(lambda o: o.value.replace("-", " ").title())
    slug = factory.Sequence(lambda n: f"value-{n}")


class ProductVariantFactory(DjangoModelFactory):
    class Meta:
        model = ProductVariant
        django_get_or_create = ("sku",)
        skip_postgeneration_save = True

    product = factory.SubFactory(ProductFactory)
    sku = factory.Sequence(lambda n: f"TEST-{n} 700-CL1")
    price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    is_active = True

    @factory.post_generation
    def attribute_values(self, create, extracted, **kwargs):
        """Attach AttributeValue instances, e.g.
        ProductVariantFactory(attribute_values=[av1, av2])."""
        if not create or not extracted:
            return
        for av in extracted:
            ProductVariantAttribute.objects.create(variant=self, attribute_value=av)


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = OrderModel

    customer = factory.SubFactory(CustomerFactory)
    guest_email = ""
    status = OrderModel.Status.PENDING
    shipping_fee = "9.90"
    shipping_address_snapshot = factory.LazyAttribute(
        lambda o: {
            "first_name": o.customer.user.first_name if o.customer else "Guest",
            "last_name": o.customer.user.last_name if o.customer else "User",
            "line1": "1 rue de la Paix",
            "city": "Paris",
            "postal_code": "75001",
            "country": "FR",
        }
    )


class GuestOrderFactory(OrderFactory):
    customer = None
    guest_email = factory.Faker("email")


class OrderLineFactory(DjangoModelFactory):
    class Meta:
        model = OrderLineModel

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductVariantFactory)
    product_name_snapshot = factory.LazyAttribute(lambda o: o.product.product.name)
    quantity = 1
    unit_price = factory.LazyAttribute(lambda o: o.product.price)
