import pytest
from django.contrib.auth import get_user_model
from accounts.models import Customer, Address
from catalog.models import Category, Product

User = get_user_model()


@pytest.fixture
def test_user(db):
    user = User.objects.create_user(
        username="test@example.com",
        email="test@example.com",
        password="testpassword123",
        first_name="Jean",
        last_name="Dupont",
    )
    Customer.objects.create(user=user)
    return user


@pytest.fixture
def authenticated_client(client, test_user):
    client.force_login(test_user)
    return client


@pytest.fixture
def test_category(db):
    return Category.objects.create(name="Road Signs", slug="road-signs")


@pytest.fixture
def test_product(db, test_category):
    return Product.objects.create(
        category=test_category,
        name="Stop Sign",
        slug="stop-sign",
        price="49.90",
        is_active=True,
    )
