"""Widget pricing."""


class WidgetError(Exception):
    """Base error for widget failures."""


def load_widget(sku: str) -> dict[str, str]:
    if not sku:
        raise WidgetError("empty sku")
    return {"sku": sku}
