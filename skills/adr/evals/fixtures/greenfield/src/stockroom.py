"""Stock counts per warehouse."""

COUNTS: dict[str, int] = {}


def receive(sku: str, quantity: int) -> int:
    COUNTS[sku] = COUNTS.get(sku, 0) + quantity
    return COUNTS[sku]
