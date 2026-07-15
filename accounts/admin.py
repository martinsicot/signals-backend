from django.contrib import admin
from .models import Customer, Address


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["__str__", "phone", "created_at"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    inlines = [AddressInline]
