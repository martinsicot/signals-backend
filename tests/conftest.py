import pytest

from tests.factories import (
    CategoryFactory,
    CRMUserFactory,
    CustomerFactory,
    OpsUserFactory,
    ProductFactory,
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
