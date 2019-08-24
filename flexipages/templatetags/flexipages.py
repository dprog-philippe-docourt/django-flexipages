from django import template
from django.utils.html import format_html
from django.utils.http import urlencode

register = template.Library()


@register.simple_tag
def tag_filter_link(tag):
    return format_html('?{0}', urlencode(dict(tag=tag.name)))
