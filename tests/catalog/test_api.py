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
class TestProductListFilters:
    url = "/api/products/"

    def test_filter_by_shape(self, client):
        ProductFactory(slug="tri-1", shape="triangle")
        ProductFactory(slug="tri-2", shape="triangle")
        ProductFactory(slug="rnd-1", shape="round")

        response = client.get(self.url, {"shape": "triangle"})

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert {r["slug"] for r in data["results"]} == {"tri-1", "tri-2"}

    def test_filter_by_classe(self, client):
        p1 = ProductFactory(slug="cl1-product", shape="round")
        p2 = ProductFactory(slug="cl2-product", shape="round")
        ProductVariantFactory(product=p1, sku="CL1-V", classe="CL1", is_active=True)
        ProductVariantFactory(product=p2, sku="CL2-V", classe="CL2", is_active=True)

        response = client.get(self.url, {"classe": "CL1"})

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["slug"] == "cl1-product"

    def test_filter_by_classe_ignores_inactive_variants(self, client):
        p = ProductFactory(slug="only-inactive-cl1", shape="round")
        ProductVariantFactory(product=p, sku="INACT-CL1", classe="CL1", is_active=False)

        response = client.get(self.url, {"classe": "CL1"})

        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_filter_by_classe_is_distinct(self, client):
        """A product with several matching variants is returned once."""
        p = ProductFactory(slug="multi-cl1", shape="round")
        ProductVariantFactory(product=p, sku="A-CL1", classe="CL1", is_active=True)
        ProductVariantFactory(product=p, sku="B-CL1", classe="CL1", is_active=True)

        response = client.get(self.url, {"classe": "CL1"})

        data = response.json()
        assert data["count"] == 1

    def test_shape_and_classe_combined(self, client):
        match = ProductFactory(slug="match", shape="triangle")
        wrong_shape = ProductFactory(slug="wrong-shape", shape="round")
        ProductVariantFactory(product=match, sku="M-CL2", classe="CL2", is_active=True)
        ProductVariantFactory(product=wrong_shape, sku="WS-CL2", classe="CL2", is_active=True)

        response = client.get(self.url, {"shape": "triangle", "classe": "CL2"})

        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["slug"] == "match"


@pytest.mark.django_db
class TestProductFiltersView:
    url = "/api/products/filters/"

    def test_returns_shapes_and_classes_keys(self, client, db):
        response = client.get(self.url)

        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"shapes", "classes"}

    def test_shapes_are_counted_and_labelled(self, client):
        ProductFactory(slug="s1", shape="square")
        ProductFactory(slug="s2", shape="square")
        ProductFactory(slug="t1", shape="triangle")

        response = client.get(self.url)

        shapes = {s["value"]: s for s in response.json()["shapes"]}
        assert shapes["square"] == {"value": "square", "label": "Indication", "count": 2}
        assert shapes["triangle"]["label"] == "Danger"
        assert shapes["triangle"]["count"] == 1

    def test_shapes_ordered_by_count_desc(self, client):
        ProductFactory(slug="r1", shape="round")
        ProductFactory(slug="r2", shape="round")
        ProductFactory(slug="r3", shape="round")
        ProductFactory(slug="tt1", shape="triangle")

        response = client.get(self.url)

        counts = [s["count"] for s in response.json()["shapes"]]
        assert counts == sorted(counts, reverse=True)

    def test_unknown_shape_excluded(self, client):
        ProductFactory(slug="u1", shape="unknown")
        ProductFactory(slug="sq", shape="square")

        response = client.get(self.url)

        values = {s["value"] for s in response.json()["shapes"]}
        assert "unknown" not in values
        assert "square" in values

    def test_unmapped_shape_excluded(self, client):
        """Shapes without a family label (e.g. octagon) are not surfaced."""
        ProductFactory(slug="oct", shape="octagon")
        ProductFactory(slug="sq2", shape="square")

        response = client.get(self.url)

        values = {s["value"] for s in response.json()["shapes"]}
        assert "octagon" not in values
        assert "square" in values

    def test_inactive_products_not_counted(self, client):
        ProductFactory(slug="active-sq", shape="square")
        ProductFactory(slug="inactive-sq", shape="square", is_active=False)

        response = client.get(self.url)

        shapes = {s["value"]: s for s in response.json()["shapes"]}
        assert shapes["square"]["count"] == 1

    def test_classes_are_static(self, client, db):
        response = client.get(self.url)

        assert response.json()["classes"] == [
            {"value": "CL1", "label": "Classe 1"},
            {"value": "CL2", "label": "Classe 2"},
        ]

    def test_filters_path_not_shadowed_by_slug_route(self, client, db):
        """`products/filters/` must resolve to the filters view, not a 404 slug."""
        response = client.get(self.url)
        assert response.status_code == 200
        assert "shapes" in response.json()


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
