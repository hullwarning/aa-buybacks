from django import template
from json import loads

register = template.Library()


@register.filter
def lookup(dictionary, key):
    return dictionary.get(key)


@register.filter
def not_empty(dictionary):
    return len(dictionary.keys()) is not 0


@register.filter
def entries(dictionary):
    return dictionary.items()


@register.filter
def json(text):
    return loads(text)
