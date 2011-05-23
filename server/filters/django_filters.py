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
def translation(lang, tag):
    # quick and dirty translation filter
    english = {
        'new': 'new',
        'random': 'random',
        'search': 'search',
        'admin': 'admin',
        'logout': 'logout',
        'contact': 'contact',
        'send': 'send',
        'report': 'report an issue',
        'lanparties': 'LAN Parties',
        'newstream': 'New stream',
        'newstream1': 'The easy way to share folders between computers, on LAN or Internet',
        'newstream2': 'Perfect for',
        'randstream': 'Random stream',
        'randstream1': 'Take a look for a random stream. What are people sharing?',
        'needtesters': 'We need testers, help us testing the',
        'pystreamcli': 'pystream client',
        'here': 'here',
        'tellme': 'tell me',
        'new': 'new',
        'sharing': 'Sharing',
        'descript': 'Description',
        'public': 'public',
        'private': 'private',
        'passwo': 'password (optional)',
        'passwp': 'password protected',
        'comments': 'Comments',
        'leavecom': 'Leave a comment!',
        'whatpys': 'What is pystream?',
        'whatpys1': 'Pystream is a web service for sharing folders between computers',
        'whatpys2': 'You can easily create a stream by using the',
        'whatpys3': 'There are three types of streams',
        'whatpys4': 'Public streams',
        'whatpys5': 'avaliables for everyone, on searches and random',
        'whatpys6': 'The easiest way to share folders with everyone',
        'whatpys7': 'Private streams',
        'whatpys8': 'hidden from searches (except from you LAN) and random, perfect for local sharing or',
        'whatpys9': 'You can also use a password to protect you private stream',
        'whatpys10': 'Offline streams',
        'whatpys11': 'LAN only, without internet connection, no searching and no random',
        'lanparties1': 'Download the',
        'lanparties2': 'create the streams and enjoy',
        'lanparties3': 'All streams (public or private) from your LAN will be shown on the',
        'lanparties4': 'main page',
        'lanparties4': 'and will be avaliable for searches (from you LAN)',
        'wherecli': 'Where can I get the pystream client?',
        'wherecli1': 'Pystream is in alpha state!',
        'wherecli2': 'Mac version have no',
        'wherecli3': 'support yet',
        'wherecli4': 'so you will need to manually open a TCP port',
        'wherecli5': 'Mac version is untested, so please report me any issue',
        'wherecli6': 'Source code is',
        'cancli': 'Can I develop my own client?',
        'cancli1': 'Off course!',
        'cancli2': 'To create a stream you only need to send a POST request to',
        'cancli3': 'with this data',
        'cancli4': 'API version',
        'cancli5': 'Your public IP',
        'cancli6': 'Your public port',
        'cancli7': 'If you develop a new client, please',
        'cancli8': "and i'll put it here",
        'cancli9': '... or you can use this form.',
        'cancli10': 'Show your creativity!',
        'reportingi': 'Reporting issues',
        'reportingi1': 'Explain your issue here',
        'nostreamsfound': 'No streams found!',
        'nocomments': 'No comments yet!',
        '403': 'Permission dennied!',
        '403c': 'You fail captcha!',
        '404': 'Page not found!',
        '500': 'Internal server error!'
    }
    spanish = {
        'new': 'nuevo',
        'random': 'aletario',
        'search': 'buscar',
        'admin': 'admin',
        'logout': 'salir',
        'contact': 'contacto',
        'send': 'enviar',
        'report': 'reportar un problema',
        'lanparties': 'LAN Parties',
        'newstream': 'Nuevo stream',
        'newstream1': 'La forma más sencilla de compartir carpetas entre ordenadores, en LAN o Internet',
        'newstream2': '¡Perfecto para',
        'randstream': 'Stream aleatorio',
        'randstream1': 'Echa un vistazo a un stream aletorio ¿Qué está compartiendo la gente?',
        'needtesters': 'Necesitamos testers, ayúdanos probando el',
        'pystreamcli': 'cliente pystream',
        'here': 'aquí',
        'tellme': 'dímelo',
        'sharing': 'Compartiendo',
        'descript': 'Descripción',
        'public': 'público',
        'private': 'privado',
        'passwo': 'contraseña (opcional)',
        'passwp': 'protegido por contraseña',
        'comments': 'Comentarios',
        'leavecom': '¡Deja un comentario!',
        'whatpys': '¿Qué es pystream?',
        'whatpys1': 'Pystream es un servicio web para compartir carpetas entre ordenadores',
        'whatpys2': 'Puedes crear un stream muy fácilmente mediante el',
        'whatpys3': 'Hay tres tipos de streams',
        'whatpys4': 'Públicos',
        'whatpys5': 'visibles para todo el mundo, en búsquedas y aleatorios',
        'whatpys6': 'La forma más sencilla de compartir carpetas con todo el mundo',
        'whatpys7': 'Privados',
        'whatpys8': 'ocultos para búsquedas (excepto desde tu LAN) y aleatorios, perfecto para',
        'whatpys9': 'Además puedes proteger tus streams privados mediante una contraseña',
        'whatpys10': 'Offline streams',
        'whatpys11': 'sólo visibles desde la red local, sin búsquedas ni aleatorios',
        'lanparties1': 'Descarga el',
        'lanparties2': 'crea los streams y disfruta',
        'lanparties3': 'Todos los streams (públicos o privados) de tu LAN se mostrarán en la',
        'lanparties4': 'página principal',
        'lanparties4': 'y estarán disponibles para búsquedas (desde tu LAN)',
        'wherecli': '¿Dónde puedo descargar el cliente pystream?',
        'wherecli1': 'Pystream se encuentra en estado alpha!',
        'wherecli2': 'La versión para Mac no tiene soporte',
        'wherecli3': 'todavía',
        'wherecli4': 'así que tendrás que abrir manualmente el puerto TCP',
        'wherecli5': 'La versión para Mac apenas ha sido provada, reportame cualquier error',
        'wherecli6': 'El código fuente está',
        'cancli': '¿Puedo desarollar mi propio cliente?',
        'cancli1': '¡Por supuesto!',
        'cancli2': 'Para crear un stream, solamente tienes que enviar una petición POST a',
        'cancli3': 'con estos datos',
        'cancli4': 'Versión de la API',
        'cancli5': 'Tu IP pública',
        'cancli6': 'Tu puerto público',
        'cancli7': 'Si creas un nuevo cliente, por favor',
        'cancli8': "y lo pondré aquí",
        'cancli9': '... o bien puedes usar este formulario.',
        'cancli10': '¡Muéstranos tu creatividad!',
        'reportingi': 'Reportar un problema',
        'reportingi1': 'Explica el problema aquí',
        'nostreamsfound': '¡No se encontraron streams!',
        'nocomments': '¡Sin comentarios!',
        '403': '¡Permiso denegado!',
        '403c': '¡Has fallado el captcha!',
        '404': '¡Página no encontrada!',
        '500': '¡Error interno del servidor!'
    }
    if lang == 'es':
        return spanish.get(tag, '¡Error de traducción!')
    else:
        return english.get(tag, 'Translation error!')
