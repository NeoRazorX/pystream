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
def truncate(value, arg):
    try:
        length = int(arg)
    except ValueError: # invalid literal for int()
        return value # Fail silently.
    if not isinstance(value, basestring):
        value = str(value)
    if (len(value) > length):
        return value[:length] + "..."
    else:
        return value

@register.filter
def show_os(ua):
    os = 'unknown'
    browser = 'unknown'
    # detecting os
    for aux in ['mac', 'iphone', 'ipad', 'ipod', 'windows', 'linux', 'android']:
        if ua.lower().find( aux ) != -1:
            os = aux
    # detecting browser
    for aux in ['safari', 'opera', 'chrome', 'firefox', 'msie']:
        if ua.lower().find( aux ) != -1:
            browser = aux
    return mark_safe('<span title="' + ua + '">' + os + '+' + browser + '</span>')

@register.filter
def show_platform(ua):
    os = 'unknown'
    # detecting os
    for aux in ['mac', 'windows', 'linux', 'ubuntu', 'debian', 'fedora', 'suse']:
        if ua.lower().find( aux ) != -1:
            os = aux
    return mark_safe('<span title="' + ua + '">' + os + '</span>')


@register.filter
def size(n):
    if n < 1024:
        return mark_safe( str(n) + ' bytes')
    elif n < (1000000):
        return mark_safe( str(n/1000) + ' KiB')
    elif n < (1000000000):
        return mark_safe( str(n/1000000) + ' MiB')
    elif n < (1000000000000):
        return mark_safe( str(n/1000000000) + ' GiB')
    else:
        return mark_safe( str(n/1000000000000) + ' TiB')

@register.filter
def pages(data):
    text = '<div class="pages"><span>' + str(data[1]) + ' elements, ' + str(data[2]) + ' pages</span>\n'
    
    # first
    if data[3] > 0:
        text += '<span><a href="' + data[0] + '0">&lt;&lt; first</a></span>\n'
    
    for pag in range(data[3] - 5, data[3]):
        if pag >= 0:
            text += '<span><a href="' + data[0] + str(pag) + '">' + str(pag) + '</a></span>\n'
    
    # current
    text += '<span id="current"><a href="' + data[0] + str(data[3]) + '">' + str(data[3]) + '</a></span>\n'
    
    # siguientes
    for pag in range(data[3] + 1, data[3] + 6):
        if pag < data[2]:
            text += '<span><a href="' + data[0] + str(pag) + '">' + str(pag) + '</a></span>\n'
    
    # last
    if data[3] < (data[2] - 1):
        text += '<span><a href="' + data[0] + str(data[2] - 1) + '">last &gt;&gt;</a></span>\n'
    
    if data[2] > 1:
        return mark_safe(text + '</div>')
    else:
        return mark_safe("")


