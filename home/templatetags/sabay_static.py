"""{% vstatic 'app/css/file.css' %} -> /static/app/css/file.css?v=<last modified>

Browsers kept serving old CSS/JS after changes (the Friends page rendered
unstyled because home.css was stale). The version changes whenever the
file does, so the browser fetches the new copy and caches it otherwise.
"""
import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def vstatic(path):
    url = static(path)
    found = finders.find(path)
    if found:
        url += f'?v={int(os.path.getmtime(found))}'
    return url
