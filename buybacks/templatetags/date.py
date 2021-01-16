from django import template

register = template.Library()


@register.filter
def time(value):
    return value.strftime("%Y-%m-%d %H:%M")
