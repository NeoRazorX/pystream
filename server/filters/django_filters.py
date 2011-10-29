#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of Pystream
# Copyright (C) 2011  Carlos Garcia Gomez  admin@pystream.com
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
from google.appengine.ext import webapp
from django.utils.safestring import mark_safe
from django.utils.timesince import timesince
from datetime import datetime, timedelta
from base import *

register = webapp.template.create_template_register()

@register.filter
def urlcode(value):
    p = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', re.DOTALL)
    value = p.sub(urlizer, value)
    # pylinks
    pylinks = re.findall(r'\[pylink\](.+?)\[/pylink\]', value)
    for link in pylinks:
        try:
            pyl = Pylink.get(link)
            if pyl:
                value = value.replace('[pylink]'+link+'[/pylink]', show_pylink(pyl))
            else:
                value = value.replace('[pylink]'+link+'[/pylink]', 'error!')
        except:
            value = value.replace('[pylink]'+link+'[/pylink]', 'error!')
    # tags
    aux_tags = re.findall(r'#[0-9a-zA-Z+_]+\b', value)
    for tag in aux_tags:
        value = value.replace(tag, show_tag(tag[1:]))
    # mentions
    aux_mentions = re.findall(r'@[0-9]+\b', value)
    for mention in aux_mentions:
        value = value.replace(mention, '<a href="#'+mention[1:]+'">'+mention+'</a>')
    return mark_safe(value)

@register.filter
def urlizer(link):
    if link.group(0)[-4:].lower() in ['.jpg', '.gif', '.png'] or link.group(0)[-5:].lower() in ['.jpeg']:
        return '<a href="'+link.group(0)+'">'+imgur(link.group(0))+'</a>'
    elif link.group(0)[:31] == 'http://www.youtube.com/watch?v=':
        return '<div><iframe width="420" height="345" src="http://www.youtube.com/embed/' + link.group(0).split('?v=')[1] + '" frameborder="0" allowfullscreen></iframe></div>'
    elif link.group(0)[:28] == 'http://www.xvideos.com/video':
        #return '<div><iframe src="http://flashservice.xvideos.com/embedframe/'+link.group(0).split('/video')[1]+'" frameborder=0 width=510 height=400 scrolling=no></iframe></div>'
        return '<a target="_Blank" href="' + link.group(0) + '">' + link.group(0) + '</a>'
    else:
        return '<a target="_Blank" href="' + link.group(0) + '">' + link.group(0) + '</a>'

@register.filter
def imgur(url=''):
    mini = '<a target="_Blank" href="' + url + '"><img class="gallery" src="' + url + '" alt="image"/></a>'
    if url[:19] == 'http://i.imgur.com/':
        aux = str(url).split('.')
        mini = '<a target="_Blank" href="' + url + '"><img class="gallery" src="http://i.imgur.' + aux[2] + 's.' + aux[3] + '" alt="imagen"/></a>'
    return mark_safe(mini)

@register.filter
def show_pylink(pyl, extra=False):
    texto = ''
    if pyl:
        if extra:
            texto = '<div class="pylink">'+pyl.get_status_html()+' &nbsp; <a target="_Blank" href="'+pyl.url+'">'+truncate(pyl.url, 60)+'</a>'
            for ori in pyl.origin:
                texto += '&nbsp; <a class="stream" href="'+ori+'">'+ori+'</a>'
            texto += '</div>'
        elif pyl.url[:11] == '/api/redir/':
            texto = '<div class="pylink"><a target="_Blank" href="'+pyl.url+'">'+pyl.get_file_name()+'</a> &nbsp; <a class="file_name" href="/search/'+pyl.get_file_name()+'">find more</a></div>'
        else:
            texto = '<div class="pylink">'+pyl.get_status_html()+' &nbsp; <a target="_Blank" href="'+pyl.url+'">'+truncate(pyl.url, 60)+'</a> &nbsp; <a class="file_name" href="/search/'+pyl.get_file_name()+'">'+pyl.get_file_name()+'</a></div>'
    return mark_safe(texto)

@register.filter
def show_tags(values):
    if values is None:
        return ''
    else:
        if len(values) > 0:
            text = '<div class="worldintags">'
            total = 0
            for tag in values:
                if total < 19 and tag[1] > 0:
                    text += show_tag(tag[0]) + ' &nbsp;'
            text += '</div>'
            return mark_safe(text)
        else:
            return ''

@register.filter
def show_tag(value):
    btools = Basic_tools()
    if len(value) > 1:
        return mark_safe('<a class="tag" href="/search/' + btools.valid_tag_name(value) + '">#' + btools.valid_tag_name(value) + '</a>')
    else:
        return ''

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
def show_os(ua, show=False):
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
    if show:
        return mark_safe('<span title="' + ua + '">' + os + '+' + browser + '</span>')
    else:
        return mark_safe(os + '+' + browser)

@register.filter
def show_platform(ua):
    os = 'unknown'
    # detecting os
    for aux in ['mac', 'windows', 'linux', 'ubuntu', 'debian', 'fedora', 'suse', 'web']:
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

@register.filter
def translation(lang, tag):
    # quick and dirty translation filter
    english = {
        '403': 'Permission dennied!',
        '403c': 'You fail captcha!',
        '404': 'Page not found!',
        '500': 'Internal server error!',
        'admin': 'admin',
        'anonymous': 'anonymous',
        'a_pass': 'password for access',
        'comments': 'comments',
        'contact': 'contact',
        'description': 'description',
        'edit': 'edit',
        'e_pass': 'password for edit',
        'help': 'help',
        'leavecom': 'Leave a comment!',
        'links': 'links',
        'localstreams': 'local streams',
        'logout': 'logout',
        'makerequest': 'make a request',
        'new': 'new',
        'noresults': 'No results!',
        'onlyadminrequest': 'only an admin can edit this request!',
        'onlyadminstream': 'only an admin can edit this stream!',
        'private': 'private',
        'public': 'public',
        'random': 'random',
        'refersearch': 'refer to this search by using this tag in your comments',
        'remove': 'remove',
        'report': 'report an issue',
        'reportingi': 'reporting issues or suggestions',
        'reportingi1': "Explain your issue or suggestion here.\nYou can leave your email to contact.",
        'reportingi2': 'If this form fails...',
        'reportingi3': 'You can send me an email <a href="mailto:admin@pystream.com">here</a>.',
        'results': 'results',
        'save': 'save',
        'search': 'search',
        'send': 'send',
        'sharefiles': 'share files',
        'sharelinks': 'share links',
        'stream': 'stream',
        'streams': 'streams',
        'request': 'request',
        'requests': 'requests',
        'worldtags': 'world in tags',
        'yourmail': 'your email'
    }
    spanish = {
        '403': '¡Permiso denegado!',
        '403c': '¡Has fallado el captcha!',
        '404': '¡Página no encontrada!',
        '500': '¡Error interno del servidor!',
        'admin': 'admin',
        'anonymous': 'anónimo',
        'a_pass': 'contraseña de acceso',
        'comments': 'comentarios',
        'contact': 'contacto',
        'description': 'descripción',
        'edit': 'editar',
        'e_pass': 'contraseña para editar',
        'help': 'ayuda',
        'leavecom': '¡Deja un comentario!',
        'links': 'enlaces',
        'localstreams': 'streams locales',
        'logout': 'salir',
        'makerequest': 'hacer una petición',
        'new': 'nuevo',
        'noresults': '¡Sin resultados!',
        'onlyadminrequest': '¡Solamente un administrador puede editar esta petición!',
        'onlyadminstream': '¡Solamente un administrador puede editar este stream!',
        'private': 'privado',
        'public': 'público',
        'random': 'aleatorio',
        'refersearch': 'haz referencia a esta búsqueda usando esta etiqueta en tus comentarios',
        'remove': 'eliminar',
        'report': 'reportar un problema',
        'reportingi': 'reportando problemas o sugerencias',
        'reportingi1': "Explica tu problema aquí.\nPuedes dejar tu email de contacto.",
        'reportingi2': 'si este formulario falla...',
        'reportingi3': 'puedes enviarme un email <a href="mailto:admin@pystream.com">aquí</a>.',
        'results': 'resultados',
        'save': 'guardar',
        'search': 'buscar',
        'send': 'enviar',
        'sharefiles': 'compartir archivos',
        'sharelinks': 'compartir enlaces',
        'stream': 'stream',
        'streams': 'streams',
        'request': 'petición',
        'requests': 'peticiones',
        'worldtags': 'el mundo en etiquetas',
        'yourmail': 'tu email'
    }
    if lang == 'es':
        return mark_safe( spanish.get(tag, '¡Error de traducción!') )
    else:
        return mark_safe( english.get(tag, 'Translation error!') )
