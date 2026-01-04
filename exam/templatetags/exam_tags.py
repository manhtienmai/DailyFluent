from django import template

register = template.Library()


@register.filter
def number_to_letter(value):
    """
    Convert số (1, 2, 3, 4) thành chữ cái (A, B, C, D).
    """
    mapping = {
        "1": "A",
        "2": "B",
        "3": "C",
        "4": "D",
        1: "A",
        2: "B",
        3: "C",
        4: "D",
    }
    return mapping.get(value, str(value))

