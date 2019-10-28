from django import template

register = template.Library()


@register.filter
def comparator_field_by_name(comparator, field_name):
    return comparator[field_name]
