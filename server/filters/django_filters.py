#!/usr/bin/env python

from google.appengine.ext import webapp
from django.utils.safestring import mark_safe

register = webapp.template.create_template_register()

@register.filter
def full_ip(n):
    d = 256 * 256 * 256
    q = []
    while d > 0:
        m,n = divmod(n,d)
        q.append(str(m))
        d = d/256
    return mark_safe( '.'.join(q) )

