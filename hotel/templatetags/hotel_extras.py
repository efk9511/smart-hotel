from django import template

register = template.Library()

@register.filter
def dict_key(d, key):
    return d.get(key)


@register.filter
def alert_class(tags):
    mapping = {
        "error": "danger",
        "debug": "secondary",
    }
    return mapping.get(tags, tags)
