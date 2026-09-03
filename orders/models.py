from django.db import models


class OrderModel(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending payment"
        PAID = "paid", "Paid"
        IN_PRODUCTION = "in_production", "In production"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    customer = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.PROTECT,
        related_name="orders",
        null=True,
        blank=True,
    )
    guest_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    shipping_fee = models.DecimalField(max_digits=8, decimal_places=2)
    shipping_address_snapshot = models.JSONField(default=dict)
    stripe_session_id = models.CharField(max_length=500, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id}"

    @property
    def contact_email(self) -> str:
        if self.customer_id:
            return self.customer.user.email
        return self.guest_email


class OrderLineModel(models.Model):
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("catalog.ProductVariant", on_delete=models.PROTECT, related_name="order_lines")
    product_name_snapshot = models.CharField(max_length=300)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        db_table = "order_lines"

    @property
    def total(self):
        return self.unit_price * self.quantity
