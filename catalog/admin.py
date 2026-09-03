from django.contrib import admin
from .models import Category, Product, Attribute, AttributeValue, ProductVariant, ProductVariantAttribute


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "base_code", "type", "category", "is_active", "created_at"]
    list_filter = ["category", "type", "is_active"]
    search_fields = ["name", "base_code"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["is_active"]
    readonly_fields = ["created_at"]


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ["attribute", "value", "display", "slug"]
    list_filter = ["attribute"]
    search_fields = ["value", "display"]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["sku", "product", "price", "is_active"]
    list_filter = ["is_active", "product__category"]
    search_fields = ["sku", "product__name"]
    list_editable = ["price", "is_active"]
