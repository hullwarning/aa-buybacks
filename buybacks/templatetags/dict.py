from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    return dictionary.get(key)


@register.filter
def not_empty(dictionary):
    return len(dictionary.keys()) is not 0
