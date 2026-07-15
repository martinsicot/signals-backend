import pytest


@pytest.mark.django_db
class TestProductListView:
    def test_api_returns_active_products(self, client, test_product):
        # Act
        response = client.get("/api/products/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["slug"] == "stop-sign"

    def test_api_filters_by_category(self, client, test_product, test_category):
        # Act
        response = client.get(f"/api/products/?category={test_category.slug}")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_api_excludes_inactive_products(self, client, test_product):
        # Arrange
        test_product.is_active = False
        test_product.save()

        # Act
        response = client.get("/api/products/")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 0


@pytest.mark.django_db
class TestProductDetailView:
    def test_api_returns_product_detail(self, client, test_product):
        # Act
        response = client.get(f"/api/products/{test_product.slug}/")

        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == "Stop Sign"
        assert "category" in response.json()

    def test_api_returns_404_for_unknown_slug(self, client):
        # Act
        response = client.get("/api/products/nonexistent-product/")

        # Assert
        assert response.status_code == 404
