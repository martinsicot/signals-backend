"""
Smoke tests: verify every factory produces a valid, persisted model instance
and that relationships and group memberships are correctly wired.
"""
import pytest

from tests.factories import (
    AddressFactory,
    CategoryFactory,
    CRMUserFactory,
    CustomerFactory,
    GuestOrderFactory,
    OpsUserFactory,
    OrderFactory,
    OrderLineFactory,
    ProductFactory,
)


@pytest.mark.django_db
class TestUserFactories:
    def test_customer_user_is_created_with_customer_profile(self):
        customer = CustomerFactory()
        assert customer.pk is not None
        assert customer.user.pk is not None
        assert customer.user.email.endswith("@example.com")

    def test_customer_user_belongs_to_customer_group(self):
        customer = CustomerFactory()
        assert customer.user.groups.filter(name="customer").exists()

    def test_customer_password_is_usable(self):
        customer = CustomerFactory()
        assert customer.user.check_password("testpassword123")

    def test_crm_user_has_no_customer_profile(self):
        user = CRMUserFactory()
        assert not hasattr(user, "customer")
        assert user.groups.filter(name="crm").exists()

    def test_ops_user_belongs_to_ops_group(self):
        user = OpsUserFactory()
        assert user.groups.filter(name="ops").exists()

    def test_two_customers_have_unique_emails(self):
        c1 = CustomerFactory()
        c2 = CustomerFactory()
        assert c1.user.email != c2.user.email


@pytest.mark.django_db
class TestAddressFactory:
    def test_address_is_linked_to_customer(self):
        address = AddressFactory()
        assert address.customer.pk is not None
        assert address.country == "FR"

    def test_explicit_customer_is_used(self):
        customer = CustomerFactory()
        address = AddressFactory(customer=customer)
        assert address.customer == customer


@pytest.mark.django_db
class TestCatalogFactories:
    def test_category_is_persisted(self):
        category = CategoryFactory()
        assert category.pk is not None
        assert category.slug.startswith("category-")

    def test_product_links_to_category(self):
        product = ProductFactory()
        assert product.category.pk is not None
        assert product.is_active is True

    def test_product_with_explicit_category(self):
        category = CategoryFactory()
        product = ProductFactory(category=category)
        assert product.category == category


@pytest.mark.django_db
class TestOrderFactories:
    def test_order_links_to_customer(self):
        order = OrderFactory()
        assert order.customer.pk is not None
        assert order.status == "pending"
        assert float(order.shipping_fee) == 9.90

    def test_order_snapshot_contains_expected_keys(self):
        order = OrderFactory()
        snapshot = order.shipping_address_snapshot
        assert "city" in snapshot
        assert "postal_code" in snapshot

    def test_guest_order_has_no_customer(self):
        order = GuestOrderFactory()
        assert order.customer is None
        assert "@" in order.guest_email

    def test_order_line_links_product_and_order(self):
        line = OrderLineFactory()
        assert line.order.pk is not None
        assert line.product.pk is not None
        assert line.product_name_snapshot == line.product.name
        assert line.total == line.unit_price * line.quantity

    def test_multiple_lines_on_same_order(self):
        order = OrderFactory()
        OrderLineFactory(order=order)
        OrderLineFactory(order=order)
        assert order.lines.count() == 2
