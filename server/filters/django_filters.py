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

@register.filter
def show_os(ua):
    os = 'unknown'
    browser = 'unknown'
    # detecting os
    for aux in ['mac', 'iphone', 'ipad', 'ipod', 'windows', 'linux', 'android']:
        if ua.lower().find( aux ) != -1:
            os = aux
    # detecting browser
    for aux in ['safari', 'opera', 'chrome', 'firefox', 'explorer']:
        if ua.lower().find( aux ) != -1:
            browser = aux
    return mark_safe('<span title="' + ua + '">' + os + '+' + browser + '</span>')

