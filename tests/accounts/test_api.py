import pytest

from tests.factories import AddressFactory, CustomerFactory


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRegisterView:
    url = "/api/auth/register/"

    def test_returns_201_on_valid_registration(self, client):
        response = client.post(self.url, data={
            "email": "new@example.com",
            "password": "securepass123",
            "first_name": "Marie",
            "last_name": "Martin",
        }, content_type="application/json")

        assert response.status_code == 201
        assert response.json()["email"] == "new@example.com"

    def test_assigns_customer_group_on_registration(self, client):
        from django.contrib.auth import get_user_model
        client.post(self.url, data={
            "email": "grouped@example.com",
            "password": "securepass123",
            "first_name": "A",
            "last_name": "B",
        }, content_type="application/json")

        user = get_user_model().objects.get(email="grouped@example.com")
        assert user.groups.filter(name="customer").exists()

    def test_returns_400_when_email_already_exists(self, client, test_user):
        response = client.post(self.url, data={
            "email": test_user.email,
            "password": "securepass123",
            "first_name": "Other",
            "last_name": "User",
        }, content_type="application/json")

        assert response.status_code == 400
        assert "email" in response.json()

    def test_returns_400_when_password_too_short(self, client):
        response = client.post(self.url, data={
            "email": "new@example.com",
            "password": "short",
            "first_name": "Marie",
            "last_name": "Martin",
        }, content_type="application/json")

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLoginView:
    url = "/api/auth/login/"

    def test_returns_200_with_valid_credentials(self, client, test_user):
        response = client.post(self.url, data={
            "email": test_user.email,
            "password": "testpassword123",
        }, content_type="application/json")

        assert response.status_code == 200
        assert response.json()["email"] == test_user.email

    def test_returns_401_with_wrong_password(self, client, test_user):
        response = client.post(self.url, data={
            "email": test_user.email,
            "password": "wrongpassword",
        }, content_type="application/json")

        assert response.status_code == 401

    def test_staff_login_returns_groups(self, client, crm_user):
        response = client.post(self.url, data={
            "email": crm_user.email,
            "password": "testpassword123",
        }, content_type="application/json")

        assert response.status_code == 200
        assert "crm" in response.json()["groups"]


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLogoutView:
    url = "/api/auth/logout/"

    def test_returns_204_when_authenticated(self, authenticated_client):
        response = authenticated_client.post(self.url)
        assert response.status_code == 204

    def test_returns_403_when_unauthenticated(self, client):
        response = client.post(self.url)
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMeView:
    url = "/api/auth/me/"

    def test_returns_customer_data_when_authenticated(self, authenticated_client, test_user):
        response = authenticated_client.get(self.url)

        assert response.status_code == 200
        assert response.json()["email"] == test_user.email

    def test_returns_staff_data_for_crm_user(self, crm_client, crm_user):
        response = crm_client.get(self.url)

        assert response.status_code == 200
        assert "crm" in response.json()["groups"]

    def test_returns_403_when_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Addresses (customer self-service)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAddressListCreateView:
    url = "/api/addresses/"

    def test_returns_empty_list_when_no_addresses(self, authenticated_client):
        response = authenticated_client.get(self.url)
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_own_addresses(self, client, customer):
        AddressFactory(customer=customer)
        AddressFactory(customer=customer)
        client.force_login(customer.user)

        response = client.get(self.url)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_does_not_return_other_customer_addresses(self, authenticated_client, test_user):
        other_customer = CustomerFactory()
        AddressFactory(customer=other_customer)

        response = authenticated_client.get(self.url)
        assert response.json() == []

    def test_creates_address_successfully(self, authenticated_client):
        response = authenticated_client.post(self.url, data={
            "first_name": "Jean",
            "last_name": "Dupont",
            "line1": "1 rue de Rivoli",
            "city": "Paris",
            "postal_code": "75001",
            "country": "FR",
        }, content_type="application/json")

        assert response.status_code == 201
        assert response.json()["city"] == "Paris"

    def test_returns_403_for_non_customer(self, crm_client):
        response = crm_client.get(self.url)
        assert response.status_code == 403

    def test_returns_403_when_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == 403
