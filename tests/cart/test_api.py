import pytest

from tests.factories import ProductVariantFactory


# ---------------------------------------------------------------------------
# Cart view — GET /api/cart/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCartView:
    url = "/api/cart/"

    def test_returns_empty_cart_by_default(self, client):
        response = client.get(self.url)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["item_count"] == 0
        assert float(data["subtotal"]) == 0

    def test_reflects_items_added_to_session(self, client):
        variant = ProductVariantFactory(price="49.90")
        client.post("/api/cart/add/", data={
            "variant_id": variant.pk,
            "quantity": 2,
        }, content_type="application/json")

        response = client.get(self.url)
        assert response.status_code == 200
        assert response.json()["item_count"] == 2


# ---------------------------------------------------------------------------
# Add — POST /api/cart/add/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCartAddView:
    url = "/api/cart/add/"

    def test_adds_product_to_cart(self, client):
        variant = ProductVariantFactory()

        response = client.post(self.url, data={
            "variant_id": variant.pk,
            "quantity": 1,
        }, content_type="application/json")

        assert response.status_code == 200

    def test_increments_quantity_on_second_add(self, client):
        variant = ProductVariantFactory()
        client.post(self.url, data={"variant_id": variant.pk, "quantity": 2},
                    content_type="application/json")
        client.post(self.url, data={"variant_id": variant.pk, "quantity": 3},
                    content_type="application/json")

        response = client.get("/api/cart/")
        assert response.json()["item_count"] == 5

    def test_add_endpoint_is_additive_and_ignores_override_flag(self, client):
        # The add endpoint always increments; replace semantics live on PATCH update.
        variant = ProductVariantFactory()
        client.post(self.url, data={"variant_id": variant.pk, "quantity": 5},
                    content_type="application/json")
        client.post(self.url, data={"variant_id": variant.pk, "quantity": 2,
                                    "override_quantity": True},
                    content_type="application/json")

        response = client.get("/api/cart/")
        assert response.json()["item_count"] == 7

    def test_returns_400_when_variant_id_missing(self, client):
        response = client.post(self.url, data={"quantity": 1},
                               content_type="application/json")
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Update — PATCH /api/cart/update/{variant_id}/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCartUpdateView:
    def test_updates_product_quantity(self, client):
        variant = ProductVariantFactory()
        client.post("/api/cart/add/", data={"variant_id": variant.pk, "quantity": 1},
                    content_type="application/json")

        response = client.patch(f"/api/cart/update/{variant.pk}/",
                                data={"quantity": 4},
                                content_type="application/json")

        assert response.status_code == 200
        assert client.get("/api/cart/").json()["item_count"] == 4

    def test_missing_quantity_removes_item(self, client):
        # A missing/zero quantity is treated as "remove" by the update endpoint.
        variant = ProductVariantFactory()
        client.post("/api/cart/add/", data={"variant_id": variant.pk, "quantity": 2},
                    content_type="application/json")

        response = client.patch(f"/api/cart/update/{variant.pk}/",
                                data={},
                                content_type="application/json")
        assert response.status_code == 200
        assert client.get("/api/cart/").json()["item_count"] == 0


# ---------------------------------------------------------------------------
# Remove — DELETE /api/cart/remove/{variant_id}/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCartRemoveView:
    def test_removes_product_from_cart(self, client):
        variant = ProductVariantFactory()
        client.post("/api/cart/add/", data={"variant_id": variant.pk, "quantity": 2},
                    content_type="application/json")

        response = client.delete(f"/api/cart/remove/{variant.pk}/")
        assert response.status_code == 204
        assert client.get("/api/cart/").json()["item_count"] == 0

    def test_removing_nonexistent_item_is_safe(self, client):
        response = client.delete("/api/cart/remove/99999/")
        assert response.status_code == 204


# ---------------------------------------------------------------------------
# Clear — DELETE /api/cart/clear/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCartClearView:
    url = "/api/cart/clear/"

    def test_clears_all_items(self, client):
        variant = ProductVariantFactory()
        client.post("/api/cart/add/", data={"variant_id": variant.pk, "quantity": 3},
                    content_type="application/json")

        response = client.delete(self.url)
        assert response.status_code == 204
        assert client.get("/api/cart/").json()["item_count"] == 0

    def test_clearing_empty_cart_is_safe(self, client):
        response = client.delete(self.url)
        assert response.status_code == 204
