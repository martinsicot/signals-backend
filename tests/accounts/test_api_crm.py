import pytest

from tests.factories import AddressFactory, CustomerFactory


# ---------------------------------------------------------------------------
# CRM — Customer list
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCRMCustomerListView:
    url = "/api/crm/customers/"

    def test_returns_all_customers_for_crm(self, crm_client):
        CustomerFactory()
        CustomerFactory()

        response = crm_client.get(self.url)
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_filters_by_email(self, crm_client):
        CustomerFactory()
        target = CustomerFactory()

        response = crm_client.get(self.url, {"email": target.user.email})
        assert response.status_code == 200
        assert all(target.user.email in r["email"] for r in response.json())

    def test_accessible_by_ops(self, ops_client):
        response = ops_client.get(self.url)
        assert response.status_code == 200

    def test_returns_403_for_customers(self, authenticated_client):
        response = authenticated_client.get(self.url)
        assert response.status_code == 403

    def test_returns_403_when_unauthenticated(self, client):
        response = client.get(self.url)
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# CRM — Customer detail
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCRMCustomerDetailView:
    def test_returns_customer_profile(self, crm_client):
        customer = CustomerFactory()

        response = crm_client.get(f"/api/crm/customers/{customer.pk}/")
        assert response.status_code == 200
        assert response.json()["email"] == customer.user.email

    def test_returns_404_for_unknown_customer(self, crm_client):
        response = crm_client.get("/api/crm/customers/99999/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# CRM — Address list / create
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCRMAddressListView:
    def test_lists_addresses_for_any_customer(self, crm_client):
        customer = CustomerFactory()
        AddressFactory(customer=customer)
        AddressFactory(customer=customer)

        response = crm_client.get(f"/api/crm/customers/{customer.pk}/addresses/")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_creates_address_for_customer(self, crm_client):
        customer = CustomerFactory()

        response = crm_client.post(
            f"/api/crm/customers/{customer.pk}/addresses/",
            data={
                "first_name": "Jean",
                "last_name": "Dupont",
                "line1": "1 rue de Rivoli",
                "city": "Paris",
                "postal_code": "75001",
                "country": "FR",
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["city"] == "Paris"

    def test_returns_403_for_ops(self, ops_client):
        customer = CustomerFactory()
        response = ops_client.post(
            f"/api/crm/customers/{customer.pk}/addresses/",
            data={},
            content_type="application/json",
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# CRM — Address detail / patch / delete
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCRMAddressDetailView:
    def test_retrieves_address(self, crm_client):
        address = AddressFactory()

        response = crm_client.get(
            f"/api/crm/customers/{address.customer.pk}/addresses/{address.pk}/"
        )
        assert response.status_code == 200
        assert response.json()["id"] == address.pk

    def test_patches_address_city(self, crm_client):
        address = AddressFactory()

        response = crm_client.patch(
            f"/api/crm/customers/{address.customer.pk}/addresses/{address.pk}/",
            data={"city": "Lyon"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["city"] == "Lyon"

    def test_deletes_address(self, crm_client):
        address = AddressFactory()

        response = crm_client.delete(
            f"/api/crm/customers/{address.customer.pk}/addresses/{address.pk}/"
        )
        assert response.status_code == 204

    def test_returns_404_when_address_belongs_to_different_customer(self, crm_client):
        address = AddressFactory()
        other_customer = CustomerFactory()

        response = crm_client.get(
            f"/api/crm/customers/{other_customer.pk}/addresses/{address.pk}/"
        )
        assert response.status_code == 404

    def test_returns_403_for_ops_on_patch(self, ops_client):
        address = AddressFactory()

        response = ops_client.patch(
            f"/api/crm/customers/{address.customer.pk}/addresses/{address.pk}/",
            data={"city": "Lyon"},
            content_type="application/json",
        )
        assert response.status_code == 403
