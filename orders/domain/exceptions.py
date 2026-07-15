class DomainError(Exception):
    pass


class EmptyOrderError(DomainError):
    def __str__(self):
        return "Order must contain at least one item."


class OrderTooLargeError(DomainError):
    def __init__(self, quantity: int, max_quantity: int):
        self.quantity = quantity
        self.max_quantity = max_quantity

    def __str__(self):
        return (
            f"Order of {self.quantity} items exceeds the maximum of "
            f"{self.max_quantity} for individual customers. Please request a quote."
        )


class ProductNotAvailableError(DomainError):
    def __init__(self, product_id: int):
        self.product_id = product_id

    def __str__(self):
        return f"Product {self.product_id} is not available."
