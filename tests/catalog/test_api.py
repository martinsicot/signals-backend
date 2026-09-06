import pytest

from tests.factories import (
    AttributeValueFactory,
    CategoryFactory,
    ProductFactory,
    ProductVariantFactory,
)


@pytest.mark.django_db
class TestProductListView:
    def test_api_returns_active_products(self, client, test_product):
        # Act
        response = client.get("/api/products/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["slug"] == "stop-sign"

    def test_api_filters_by_category(self, client, test_product, test_category):
        # Act
        response = client.get(f"/api/products/?category={test_category.slug}")

        # Assert
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_api_excludes_inactive_products(self, client, test_product):
        # Arrange
        test_product.is_active = False
        test_product.save()

        # Act
        response = client.get("/api/products/")

        # Assert
        assert response.status_code == 200
        assert response.json()["count"] == 0


@pytest.mark.django_db
class TestProductListPagination:
    url = "/api/products/"

    def test_response_has_pagination_envelope(self, client, test_product):
        response = client.get(self.url)

        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"count", "next", "previous", "results"}

    def test_page_size_is_24(self, client):
        ProductFactory.create_batch(30)

        response = client.get(self.url)

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 30
        assert len(data["results"]) == 24

    def test_next_link_present_when_more_pages(self, client):
        ProductFactory.create_batch(30)

        response = client.get(self.url)

        data = response.json()
        assert data["next"] is not None
        assert data["previous"] is None

    def test_second_page_returns_remaining_products(self, client):
        ProductFactory.create_batch(30)

        response = client.get(self.url, {"page": 2})

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 6
        assert data["next"] is None
        assert data["previous"] is not None

    def test_single_page_has_no_next_or_previous(self, client):
        ProductFactory.create_batch(5)

        response = client.get(self.url)

        data = response.json()
        assert data["count"] == 5
        assert data["next"] is None
        assert data["previous"] is None

    def test_out_of_range_page_returns_404(self, client):
        ProductFactory.create_batch(5)

        response = client.get(self.url, {"page": 99})

        assert response.status_code == 404

    def test_pagination_preserves_filters_in_links(self, client):
        cat = CategoryFactory(slug="cat-paginated")
        ProductFactory.create_batch(30, category=cat)

        response = client.get(self.url, {"category": "cat-paginated"})

        data = response.json()
        assert data["count"] == 30
        assert "category=cat-paginated" in data["next"]


@pytest.mark.django_db
class TestProductSearchView:
    url = "/api/products/"

    def test_returns_matching_products_by_name(self, client):
        ProductFactory(name="Panneau Stop", slug="panneau-stop")
        ProductFactory(name="Panneau Cédez", slug="panneau-cedez")

        response = client.get(self.url, {"q": "stop"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["slug"] == "panneau-stop"

    def test_returns_matching_products_by_description(self, client):
        ProductFactory(slug="p1", description="panneau octogonal rouge obligatoire")
        ProductFactory(slug="p2", description="panneau triangulaire danger")

        response = client.get(self.url, {"q": "octogonal"})
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_search_is_case_insensitive(self, client):
        ProductFactory(name="Panneau Stop", slug="panneau-stop-ci")

        response = client.get(self.url, {"q": "STOP"})
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_returns_empty_list_when_no_match(self, client):
        ProductFactory(name="Panneau Stop", slug="panneau-stop-nomatch")

        response = client.get(self.url, {"q": "cédez"})
        assert response.status_code == 200
        assert response.json()["results"] == []

    def test_blank_q_returns_all_products(self, client):
        ProductFactory(slug="p-a")
        ProductFactory(slug="p-b")

        response = client.get(self.url, {"q": "  "})
        assert response.status_code == 200
        assert response.json()["count"] >= 2

    def test_search_combined_with_category_filter(self, client):
        cat_a = CategoryFactory(slug="cat-a")
        cat_b = CategoryFactory(slug="cat-b")
        ProductFactory(name="Stop FR", slug="stop-fr", category=cat_a)
        ProductFactory(name="Stop ES", slug="stop-es", category=cat_b)

        response = client.get(self.url, {"q": "stop", "category": "cat-a"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["slug"] == "stop-fr"

    def test_excludes_inactive_products_from_search(self, client):
        ProductFactory(name="Panneau Stop", slug="stop-inactive", is_active=False)

        response = client.get(self.url, {"q": "stop"})
        assert response.status_code == 200
        assert response.json()["results"] == []


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

    def test_detail_includes_variants_with_attributes(self, client, test_variant):
        # Act
        response = client.get(f"/api/products/{test_variant.product.slug}/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["variants"]) == 1
        variant = data["variants"][0]
        assert variant["sku"] == "STOP-700-CL2"
        assert variant["price"] == "49.90"
        attrs = {a["attribute_slug"]: a for a in variant["attributes"]}
        assert set(attrs) == {"taille", "classe"}
        assert attrs["taille"]["display"] == "700 mm"
        assert attrs["classe"]["attribute_name"] == "Classe"
        assert attrs["classe"]["display"] == "Classe 2"


@pytest.mark.django_db
class TestProductListMinPrice:
    def test_min_price_reflects_cheapest_active_variant(self, client, test_product):
        # Arrange
        ProductVariantFactory(product=test_product, sku="V-CHEAP", price="19.90")
        ProductVariantFactory(product=test_product, sku="V-PRICEY", price="99.00")

        # Act
        response = client.get("/api/products/")

        # Assert
        assert response.status_code == 200
        row = next(p for p in response.json()["results"] if p["slug"] == test_product.slug)
        assert row["min_price"] == "19.90"

    def test_min_price_is_null_when_no_priced_variant(self, client, test_product):
        # Arrange
        ProductVariantFactory(product=test_product, sku="V-NOPRICE", price=None)

        # Act
        response = client.get("/api/products/")

        # Assert
        row = next(p for p in response.json()["results"] if p["slug"] == test_product.slug)
        assert row["min_price"] is None


@pytest.mark.django_db
class TestVariantDetailView:
    def test_returns_variant_with_product_and_attributes(self, client, test_variant):
        # Act
        response = client.get(f"/api/variants/{test_variant.id}/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == "STOP-700-CL2"
        assert data["product_name"] == "Stop Sign"
        assert data["product_slug"] == "stop-sign"
        assert {a["attribute_slug"] for a in data["attributes"]} == {"taille", "classe"}

    def test_returns_404_for_unknown_id(self, client, db):
        response = client.get("/api/variants/999999/")
        assert response.status_code == 404

    def test_excludes_inactive_variant(self, client, test_product):
        # Arrange
        variant = ProductVariantFactory(
            product=test_product, sku="V-INACTIVE", price="10.00", is_active=False
        )

        # Act
        response = client.get(f"/api/variants/{variant.id}/")

        # Assert
        assert response.status_code == 404


@pytest.mark.django_db
class TestVariantDisplayName:
    def test_display_name_joins_product_and_attribute_displays(self, test_product):
        # Arrange
        size = AttributeValueFactory(
            attribute__name="Taille", attribute__slug="taille",
            value="600x600", display="600×600 mm", slug="600x600",
        )
        finition = AttributeValueFactory(
            attribute__name="Finition", attribute__slug="finition",
            value="ALU", display="Aluminium", slug="alu",
        )
        variant = ProductVariantFactory(
            product=test_product, sku="STOP-600-ALU",
            attribute_values=[size, finition],
        )

        # Assert — ordered by attribute name: Finition, then Taille
        assert variant.display_name == "Stop Sign — Aluminium — 600×600 mm"
