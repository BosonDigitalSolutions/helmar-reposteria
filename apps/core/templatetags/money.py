from django import template

from apps.core.money import pesos as format_pesos

register = template.Library()


@register.filter
def pesos(value):
    if value is None or value == "":
        return ""
    return format_pesos(value)
