"""Synthetic company code for the offline demo; no real employee data."""


def calculate_total(unit_price: int, quantity: int) -> int:
    """Return the total in cents for a valid order."""
    if unit_price < 0 or quantity < 1:
        raise ValueError("Order price and quantity are invalid")
    return unit_price * quantity


def format_order_id(number: int) -> str:
    """Format a positive order number for display."""
    if number < 1:
        raise ValueError("Order number must be positive")
    return f"ORD-{number:06d}"
