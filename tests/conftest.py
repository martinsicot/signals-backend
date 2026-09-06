import pytest

from tests.factories import (
    AttributeValueFactory,
    CategoryFactory,
    CRMUserFactory,
    CustomerFactory,
    OpsUserFactory,
    ProductFactory,
    ProductVariantFactory,
)


@pytest.fixture
def customer(db):
    return CustomerFactory()


@pytest.fixture
def test_user(db):
    """Customer user — kept for backward compat with existing tests."""
    return CustomerFactory().user


@pytest.fixture
def authenticated_client(client, test_user):
    client.force_login(test_user)
    return client


@pytest.fixture
def crm_user(db):
    return CRMUserFactory()


@pytest.fixture
def crm_client(client, crm_user):
    client.force_login(crm_user)
    return client


@pytest.fixture
def ops_user(db):
    return OpsUserFactory()


@pytest.fixture
def ops_client(client, ops_user):
    client.force_login(ops_user)
    return client


@pytest.fixture
def test_category(db):
    return CategoryFactory(name="Road Signs", slug="road-signs")


@pytest.fixture
def test_product(db, test_category):
    return ProductFactory(
        category=test_category,
        name="Stop Sign",
        slug="stop-sign",
    )


@pytest.fixture
def test_variant(db, test_product):
    """A priced, active variant of test_product with two attribute values."""
    size = AttributeValueFactory(
        attribute__name="Taille",
        attribute__slug="taille",
        value="700",
        display="700 mm",
        slug="700",
    )
    cls = AttributeValueFactory(
        attribute__name="Classe",
        attribute__slug="classe",
        value="CL2",
        display="Classe 2",
        slug="cl2",
    )
    return ProductVariantFactory(
        product=test_product,
        sku="STOP-700-CL2",
        price="49.90",
        is_active=True,
        attribute_values=[size, cls],
    )
