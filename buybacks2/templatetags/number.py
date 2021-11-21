from django import template

register = template.Library()


@register.filter
def format_number(value, p=1):
    """return a formated number with thousands seperators"""
    try:
        return f"{float(value):,.{int(p)}f}"
    except (ValueError, TypeError):
        return None
