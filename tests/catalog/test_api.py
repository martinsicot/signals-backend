import pytest

from tests.factories import CategoryFactory, ProductFactory


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
class TestProductSearchView:
    url = "/api/products/"

    def test_returns_matching_products_by_name(self, client):
        ProductFactory(name="Panneau Stop", slug="panneau-stop")
        ProductFactory(name="Panneau Cédez", slug="panneau-cedez")

        response = client.get(self.url, {"q": "stop"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["slug"] == "panneau-stop"

    def test_returns_matching_products_by_description(self, client):
        ProductFactory(slug="p1", description="panneau octogonal rouge obligatoire")
        ProductFactory(slug="p2", description="panneau triangulaire danger")

        response = client.get(self.url, {"q": "octogonal"})
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_search_is_case_insensitive(self, client):
        ProductFactory(name="Panneau Stop", slug="panneau-stop-ci")

        response = client.get(self.url, {"q": "STOP"})
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_returns_empty_list_when_no_match(self, client):
        ProductFactory(name="Panneau Stop", slug="panneau-stop-nomatch")

        response = client.get(self.url, {"q": "cédez"})
        assert response.status_code == 200
        assert response.json() == []

    def test_blank_q_returns_all_products(self, client):
        ProductFactory(slug="p-a")
        ProductFactory(slug="p-b")

        response = client.get(self.url, {"q": "  "})
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_search_combined_with_category_filter(self, client):
        cat_a = CategoryFactory(slug="cat-a")
        cat_b = CategoryFactory(slug="cat-b")
        ProductFactory(name="Stop FR", slug="stop-fr", category=cat_a)
        ProductFactory(name="Stop ES", slug="stop-es", category=cat_b)

        response = client.get(self.url, {"q": "stop", "category": "cat-a"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["slug"] == "stop-fr"

    def test_excludes_inactive_products_from_search(self, client):
        ProductFactory(name="Panneau Stop", slug="stop-inactive", is_active=False)

        response = client.get(self.url, {"q": "stop"})
        assert response.status_code == 200
        assert response.json() == []


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
