from django.contrib import admin
from .models import OrderModel, OrderLineModel


class OrderLineInline(admin.TabularInline):
    model = OrderLineModel
    extra = 0
    readonly_fields = ["product", "product_name_snapshot", "quantity", "unit_price", "total"]
    can_delete = False


@admin.register(OrderModel)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "contact_email", "status", "shipping_fee", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["customer__user__email", "guest_email", "stripe_session_id"]
    readonly_fields = ["stripe_session_id", "shipping_address_snapshot", "created_at", "updated_at"]
    inlines = [OrderLineInline]
    list_select_related = ["customer__user"]
