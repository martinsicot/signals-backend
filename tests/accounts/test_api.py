import pytest

from tests.factories import AddressFactory, CustomerFactory


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRegisterView:
    url = "/api/auth/register/"

    def test_returns_201_with_token_pair(self, client):
        response = client.post(self.url, data={
            "email": "new@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
            "first_name": "Marie",
            "last_name": "Martin",
        }, content_type="application/json")

        assert response.status_code == 201
        body = response.json()
        assert body["access"]
        assert body["refresh"]

    def test_assigns_customer_group_on_registration(self, client):
        from django.contrib.auth import get_user_model
        client.post(self.url, data={
            "email": "grouped@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
            "first_name": "A",
            "last_name": "B",
        }, content_type="application/json")

        user = get_user_model().objects.get(email="grouped@example.com")
        assert user.groups.filter(name="customer").exists()

    def test_returns_400_when_email_already_exists(self, client, test_user):
        response = client.post(self.url, data={
            "email": test_user.email,
            "password": "securepass123",
            "password_confirm": "securepass123",
            "first_name": "Other",
            "last_name": "User",
        }, content_type="application/json")

        assert response.status_code == 400
        assert "email" in response.json()

    def test_returns_400_when_password_too_short(self, client):
        response = client.post(self.url, data={
            "email": "new@example.com",
            "password": "short",
            "password_confirm": "short",
            "first_name": "Marie",
            "last_name": "Martin",
        }, content_type="application/json")

        assert response.status_code == 400

    def test_returns_400_when_passwords_do_not_match(self, client):
        response = client.post(self.url, data={
            "email": "mismatch@example.com",
            "password": "securepass123",
            "password_confirm": "different456",
            "first_name": "Marie",
            "last_name": "Martin",
        }, content_type="application/json")

        assert response.status_code == 400
        assert "password_confirm" in response.json()


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLoginView:
    url = "/api/auth/login/"

    def test_returns_200_with_token_pair_and_user(self, client, test_user):
        response = client.post(self.url, data={
            "email": test_user.email,
            "password": "testpassword123",
        }, content_type="application/json")

        assert response.status_code == 200
        body = response.json()
        assert body["access"]
        assert body["refresh"]
        assert body["user"]["email"] == test_user.email

    def test_returns_401_with_wrong_password(self, client, test_user):
        response = client.post(self.url, data={
            "email": test_user.email,
            "password": "wrongpassword",
        }, content_type="application/json")

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid credentials."}

    def test_staff_login_returns_groups(self, client, crm_user):
        response = client.post(self.url, data={
            "email": crm_user.email,
            "password": "testpassword123",
        }, content_type="application/json")

        assert response.status_code == 200
        assert "crm" in response.json()["user"]["groups"]


def _obtain_tokens(client, email, password="testpassword123"):
    """Log in through the API and return the (access, refresh) token pair."""
    response = client.post(
        "/api/auth/login/",
        data={"email": email, "password": password},
        content_type="application/json",
    )
    body = response.json()
    return body["access"], body["refresh"]


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLogoutView:
    url = "/api/auth/logout/"

    def test_returns_205_and_blacklists_refresh(self, client, test_user):
        access, refresh = _obtain_tokens(client, test_user.email)

        response = client.post(
            self.url,
            data={"refresh": refresh},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        assert response.status_code == 205

        # The blacklisted refresh token can no longer be refreshed.
        refresh_response = client.post(
            "/api/auth/token/refresh/",
            data={"refresh": refresh},
            content_type="application/json",
        )
        assert refresh_response.status_code == 401

    def test_returns_400_when_refresh_missing(self, client, test_user):
        access, _ = _obtain_tokens(client, test_user.email)

        response = client.post(
            self.url,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        assert response.status_code == 400
        assert "refresh" in response.json()

    def test_returns_400_with_invalid_refresh(self, client, test_user):
        access, _ = _obtain_tokens(client, test_user.email)

        response = client.post(
            self.url,
            data={"refresh": "not-a-real-token"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        assert response.status_code == 400

    def test_returns_401_when_unauthenticated(self, client):
        response = client.post(self.url)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTokenRefreshView:
    url = "/api/auth/token/refresh/"

    def test_returns_new_access_token(self, client, test_user):
        _, refresh = _obtain_tokens(client, test_user.email)

        response = client.post(
            self.url,
            data={"refresh": refresh},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["access"]

    def test_returns_401_with_invalid_refresh(self, client):
        response = client.post(
            self.url,
            data={"refresh": "garbage"},
            content_type="application/json",
        )
        assert response.status_code == 401


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

    def test_returns_401_when_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Account profile (GET / PATCH /api/account/me/)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProfileView:
    url = "/api/account/me/"

    def test_returns_401_when_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == 401

    def test_returns_403_for_non_customer(self, crm_client):
        response = crm_client.get(self.url)
        assert response.status_code == 403

    def test_get_returns_profile_shape(self, client, customer):
        AddressFactory(
            customer=customer,
            line1="12 rue des Acacias",
            line2="",
            postal_code="75001",
            city="Paris",
            country="FR",
            is_default=True,
        )
        client.force_login(customer.user)

        response = client.get(self.url)
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == customer.user.id
        assert body["email"] == customer.user.email
        assert body["phone"] == customer.phone
        assert body["default_shipping_address"] == {
            "line1": "12 rue des Acacias",
            "line2": "",
            "zip_code": "75001",
            "city": "Paris",
            "country": "FR",
        }

    def test_get_returns_null_address_when_none(self, authenticated_client):
        response = authenticated_client.get(self.url)
        assert response.status_code == 200
        assert response.json()["default_shipping_address"] is None

    def test_patch_updates_name_and_phone(self, client, customer):
        client.force_login(customer.user)

        response = client.patch(self.url, data={
            "first_name": "Martin",
            "last_name": "Sicot",
            "phone": "0612345678",
        }, content_type="application/json")

        assert response.status_code == 200
        body = response.json()
        assert body["first_name"] == "Martin"
        assert body["last_name"] == "Sicot"
        assert body["phone"] == "0612345678"

        customer.refresh_from_db()
        customer.user.refresh_from_db()
        assert customer.user.first_name == "Martin"
        assert customer.phone == "0612345678"

    def test_patch_email_is_ignored(self, client, customer):
        original_email = customer.user.email
        client.force_login(customer.user)

        response = client.patch(self.url, data={
            "email": "hacker@example.com",
        }, content_type="application/json")

        assert response.status_code == 200
        assert response.json()["email"] == original_email
        customer.user.refresh_from_db()
        assert customer.user.email == original_email

    def test_patch_creates_default_address_when_none(self, client, customer):
        client.force_login(customer.user)

        response = client.patch(self.url, data={
            "default_shipping_address": {
                "line1": "1 rue de Rivoli",
                "zip_code": "75004",
                "city": "Paris",
                "country": "FR",
            },
        }, content_type="application/json")

        assert response.status_code == 200
        assert response.json()["default_shipping_address"]["zip_code"] == "75004"

        address = customer.addresses.get()
        assert address.postal_code == "75004"
        assert address.is_default is True

    def test_patch_updates_existing_default_address(self, client, customer):
        AddressFactory(customer=customer, postal_code="75001", is_default=True)
        client.force_login(customer.user)

        response = client.patch(self.url, data={
            "default_shipping_address": {
                "line1": "9 avenue des Champs",
                "zip_code": "75008",
                "city": "Paris",
            },
        }, content_type="application/json")

        assert response.status_code == 200
        assert customer.addresses.count() == 1
        address = customer.addresses.get()
        assert address.postal_code == "75008"
        assert address.line1 == "9 avenue des Champs"


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

    def test_returns_401_when_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPasswordResetRequestView:
    url = "/api/auth/password-reset/"

    def test_sends_email_for_known_address(self, client, test_user, mailoutbox):
        response = client.post(self.url, data={
            "email": test_user.email,
        }, content_type="application/json")

        assert response.status_code == 200
        assert len(mailoutbox) == 1
        assert test_user.email in mailoutbox[0].to

    def test_returns_200_for_unknown_address_without_email(self, client, mailoutbox):
        response = client.post(self.url, data={
            "email": "nobody@example.com",
        }, content_type="application/json")

        # Always 200 to avoid account enumeration, but no email is sent.
        assert response.status_code == 200
        assert len(mailoutbox) == 0

    def test_returns_400_when_email_missing(self, client):
        response = client.post(self.url, data={}, content_type="application/json")

        assert response.status_code == 400
        assert "email" in response.json()


@pytest.mark.django_db
class TestPasswordResetConfirmView:
    url = "/api/auth/password-reset/confirm/"

    def _uid_and_token(self, user):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        return (
            urlsafe_base64_encode(force_bytes(user.pk)),
            default_token_generator.make_token(user),
        )

    def test_resets_password_with_valid_token(self, client, test_user):
        uid, token = self._uid_and_token(test_user)

        response = client.post(self.url, data={
            "uid": uid,
            "token": token,
            "new_password": "brandnewpass456",
        }, content_type="application/json")

        assert response.status_code == 200
        test_user.refresh_from_db()
        assert test_user.check_password("brandnewpass456")

    def test_returns_400_with_invalid_token(self, client, test_user):
        uid, _ = self._uid_and_token(test_user)

        response = client.post(self.url, data={
            "uid": uid,
            "token": "invalid-token",
            "new_password": "brandnewpass456",
        }, content_type="application/json")

        assert response.status_code == 400
        assert "detail" in response.json()

    def test_returns_400_when_fields_missing(self, client):
        response = client.post(self.url, data={}, content_type="application/json")

        assert response.status_code == 400
        assert "detail" in response.json()
