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

from google.appengine.ext import webapp
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta

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
def show_platform(ua, show=False):
    os = 'unknown'
    # detecting os
    for aux in ['mac', 'windows', 'linux', 'ubuntu', 'debian', 'fedora', 'suse', 'web']:
        if ua.lower().find( aux ) != -1:
            os = aux
    if show:
        return mark_safe('<span title="' + ua + '">' + os + '</span>')
    else:
        return mark_safe(os)


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
def stream_time_left(date, strikes):
    if strikes < 0:
        rdate = date - datetime.today() - timedelta(hours=24)
    else:
        rdate = date - datetime.today() - timedelta(hours=12)
    return mark_safe('This stream will be removed after '+str( rdate.seconds/3600 )+' hours.')

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
def translation(lang, num):
    # quick and dirty translation filter
    english = ['new', 'random', 'search', 'admin', 'logout', 'contact', 'report an issue',
        'New stream', 'Random stream', 'The easy way to share data between computers, on LAN or Internet',
        'Perfect for', 'LAN Parties', 'Take a look for a random stream. What are people sharing?',
        'What is pystream?', 'Pystream is a web service for sharing folders between computers',
        'You can easily create a stream by using the', 'pystream client', 'There are three types of streams:',
        'Public streams', 'avaliables for everyone, on searches and random', 'The easiest way to share folders with everyone',
        'Private streams', 'hidden from searches (except from you LAN) and random, perfect for local sharing or',
        'You can also use a password to protect you private stream', 'Offline streams',
        'LAN only, without internet connection, no searching and no random',
        'Download the', 'create the streams and enjoy',
        'All streams (public or private) from your LAN will be shown on the', 'main page',
        'and will be avaliable for searches (from you LAN)', 'Where can I get the pystream client?',
        'Pystream is in alpha state!', 'Mac version have no', 'support yet',
        'so you will need to manually open a TCP port in Mac version',
        'Mac version is untested, so please report me any issue', 'Source code is', 'here',
        'Report any issue you have', 'Can I develop my own client?', 'Off course!',
        'To create a stream you only need to send a POST request to', 'with this data', 'API version',
        'Your public IP', 'Your public port', 'If you develop a new client, please', 'tell me', "and i'll put it here",
        '... or you can use this form.', 'Show your creativity!', 'send', 'Sharing']
    spanish = ['nuevo', 'aleatorio', 'buscar', 'admin', 'salir', 'contacto', 'reportar un problema', 'Nuevo stream',
        'Stream aleatorio', 'La forma más fácil de compartir datos entre ordenadores, en LAN o Internet',
        '¡Perfecto para', 'LAN Parties', 'Echa un vistazo a un stream aleatorio ¿Qué está compartiendo la gente?',
        'Qué es pystream?', 'Pystream es un servicio web para compartir carpetas entre ordenadores',
        'Puedes crear facilmente un stream mediante el', 'cliente pystream', 'Hay tres tipos de streams',
        'Streans públicos', 'visibles para todo el mundo, en búsquedas y aleatorios',
        'La forma más sencilla de compartir carpetas con todo el mundo',
        'Streams privados', 'ocultos para búsquedas (excepto desde tu LAN) y aleatorios, perfecto para compartir localmente o en',
        'También puedes usar una contraseña para proteger tu stream privado', 'Streams offline',
        'Solo LAN, sin conexión a internet, sin búsquedas ni aleatorios',
        'Descarga el', 'crea los streams y disfruta',
        'Todos los streams (públicos o privados) procedentes de tu LAN se mostrarán en la', 'página principal',
        'y estarán disponibles para búsquedas (desde tu LAN)', '¿Dónde puedo descargar el cliente pystream?',
        '¡Pystream está en estado alpha!', 'La versión para Mac aún no tiene soporte', '',
        'así que tendrás que abrir el puerto TCP manualmente',
        'La versión para Mac está sin probar, por favor, reportame cualquier problema que tengas',
        'El código fuente está', 'aquí', 'Reportame cualquier problema que tengas',
        '¿Puedo desarrollar mi propio cliente?', '¡Por supuesto!',
        'Para crear un stream sólo necesitas enviar una petición POST a', 'con estos datos', 'Versión de la API',
        'Tu IP pública', 'Tu puerto público', 'Si creas un nuevo cliente, por favor,', 'dimelo', 'y lo pongo aquí',
        '... o bien puedes usar este formulario', '¡Muestranos tu creatividad!', 'enviar', 'Compartiendo']
    try:
        if lang == 'es':
            return spanish[num]
        else:
            return english[num]
    except:
        return 'Translation error!'
