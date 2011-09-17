#!/usr/bin/env python
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

import cgi, os, random, Cookie, math, re

# loading django 1.2
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')
from google.appengine.ext.webapp import template

from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from recaptcha.client import captcha
from base import *


class Main_page(Basic_page, Basic_tools):
    def get(self):
        st = Stat_cache()
        template_values = {
            'title': 'Pystream: anonymous community',
            'title2': 'Anonymous community',
            'description': "The easy way to share files or links. Can't find a file? make a request!",
            'onload': 'document.search.query.focus()',
            'tags': st.get_searches(),
            'local_streams': self.streams_from_ip( self.request.remote_addr ),
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/'),
            'lang': self.get_lang()
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
        self.response.out.write( template.render(path, template_values) )


class Download_page(Basic_page, Basic_tools):
    def get(self):
        if self.request.get('os'):
            st = Stat_cache()
            st.put_download( self.request.get('os') ) # +1 to downloads
        template_values = {
            'title': 'Download pystream sharing tool',
            'title2': 'Download pystream sharing tool',
            'description': 'Download pystream sharing tool, sharing folders made easy.',
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/'),
            'user_os': self.get_os( self.request.environ['HTTP_USER_AGENT'] ),
            'lang': self.get_lang(),
            'windows_client_url': WINDOWS_CLIENT_URL,
            'linux_client_url': LINUX_CLIENT_URL,
            'mac_client_url': MAC_CLIENT_URL,
            'download_os': self.request.get('os'),
            'onload': 'download()',
        }
        if self.request.get('os'):
            path = os.path.join(os.path.dirname(__file__), 'templates/download2.html')
        else:
            path = os.path.join(os.path.dirname(__file__), 'templates/download.html')
        self.response.out.write( template.render(path, template_values) )


class New_page(Basic_page, Basic_tools):
    def get(self):
        template_values = {
            'title': 'Pystream: new page',
            'title2': 'Anonymous community',
            'description': "The easy way to share files or links. Can't find a file? make a request!",
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/'),
            'lang': self.get_lang()
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/new.html')
        self.response.out.write( template.render(path, template_values) )


class New_stream_page(Basic_page, Basic_tools):
    def get(self):
        chtml = captcha.displayhtml(
                    public_key = RECAPTCHA_PUBLIC_KEY,
                    use_ssl = False,
                    error = None)
        template_values = {
            'title': 'Sharing links on pystream',
            'title2': 'Sharing links',
            'description': 'Sahring links form.',
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/'),
            'lang': self.get_lang(),
            'captcha': chtml
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/new_stream.html')
        self.response.out.write( template.render(path, template_values) )
    
    def post(self):
        if self.request.get('description'):
            challenge = self.request.get('recaptcha_challenge_field')
            response  = self.request.get('recaptcha_response_field')
            remoteip  = self.request.remote_addr
            cResponse = captcha.submit(challenge,
                                       response,
                                       RECAPTCHA_PRIVATE_KEY,
                                       remoteip)
            if cResponse.is_valid or users.is_current_user_admin():
                    s = Stream()
                    s.description = cgi.escape( self.request.get('description') )
                    s.ip = self.request.remote_addr
                    s.os = self.request.environ['HTTP_USER_AGENT']
                    if self.request.get('public') == 'True':
                        s.status = 91
                    elif self.request.get('a_pass'):
                        s.access_pass = self.request.get('a_pass')
                        s.status = 93
                    else:
                        s.status = 92
                    if self.request.get('e_pass'):
                        s.edit_pass = self.request.get('e_pass')
                    s.put()
                    # pylinks
                    if self.request.get('links'):
                        aux_links = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', self.request.get('links'))
                        s.pylinks = self.new_pylinks(aux_links, s.get_link())
                    # searches
                    if s.status in [1, 11, 91]:
                        aux_tags = []
                        for tag in re.findall(r'#[0-9a-zA-Z+_]*', s.description):
                            aux_tags.append( tag[1:] )
                        self.tags2cache( aux_tags )
                        s.tags = self.page2search(s.get_link(), s.description, 'stream', s.date)
                        s.put()
                    else:
                        s.put()
                    # stats
                    st = Stat_cache()
                    st.put_page('stream')
                    st.put_page('pylinks', len(s.pylinks))
                    self.redirect( s.get_link() )
            else:
                self.redirect('/error/403c')
        else:
            self.redirect('/error/403')


class New_request_page(Basic_page, Basic_tools):
    def get(self):
        chtml = captcha.displayhtml(
                    public_key = RECAPTCHA_PUBLIC_KEY,
                    use_ssl = False,
                    error = None)
        template_values = {
            'title': 'Making a request on pystream',
            'title2': 'Making a request',
            'description': 'Making a new request form.',
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/'),
            'lang': self.get_lang(),
            'captcha': chtml
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/new_request.html')
        self.response.out.write( template.render(path, template_values) )
    
    def post(self):
        if self.request.get('description'):
            challenge = self.request.get('recaptcha_challenge_field')
            response  = self.request.get('recaptcha_response_field')
            remoteip  = self.request.remote_addr
            cResponse = captcha.submit(challenge,
                                       response,
                                       RECAPTCHA_PRIVATE_KEY,
                                       remoteip)
            if cResponse.is_valid or users.is_current_user_admin():
                try:
                    r = Request()
                    r.description = cgi.escape( self.request.get('description') )
                    r.ip = self.request.remote_addr
                    r.os = self.request.environ['HTTP_USER_AGENT']
                    if self.request.get('email'):
                        r.email = self.request.get('email')
                    if self.request.get('e_pass'):
                        r.edit_pass = self.request.get('e_pass')
                    r.put()
                    # searches
                    aux_tags = []
                    for tag in re.findall(r'#[0-9a-zA-Z+_]*', r.description):
                        aux_tags.append( tag[1:] )
                    self.tags2cache( aux_tags )
                    r.tags = self.page2search(r.get_link(), r.description, 'request', r.date)
                    r.put()
                    # stats
                    st = Stat_cache()
                    st.put_page('request')
                    self.redirect( r.get_link() )
                except:
                    logging.error('Cant save request!')
                    self.redirect('/error/500')
            else:
                self.redirect('/error/403c')
        else:
            self.redirect('/error/403')


class Stream_page(Basic_page, Basic_tools):
    def get(self, ids=None):
        try:
            s = Stream.get_by_id( int( ids ) )
        except:
            s = None
        
        if s: # stream exists
            if s.status not in [3, 13, 93]:
                chtml = captcha.displayhtml(
                    public_key = RECAPTCHA_PUBLIC_KEY,
                    use_ssl = False,
                    error = None)
                template_values = {
                    'title': 'Stream ' + str( s.key().id() ),
                    'description': s.description,
                    'stream': s,
                    'captcha': chtml,
                    'admin': users.is_current_user_admin(),
                    'logout': users.create_logout_url('/'),
                    'lang': self.get_lang()
                }
                path = os.path.join(os.path.dirname(__file__), 'templates/stream.html')
                self.response.out.write( template.render(path, template_values) )
            else:
                self.redirect( s.get_link() )
        elif ids: # stream selected but not found
            self.redirect('/error/404')
        else: # no stream selected
            self.redirect('/new')


class Protected_stream_page(Basic_page, Basic_tools):
    def get(self, ids=None):
        try:
            s = Stream.get_by_id( int( ids ) )
        except:
            s = None
        
        if s: # stream exists
            if self.user_gives_password(s):
                chtml = captcha.displayhtml(
                    public_key = RECAPTCHA_PUBLIC_KEY,
                    use_ssl = False,
                    error = None)
                template_values = {
                    'title': 'Stream ' + str( s.key().id() ),
                    'description': s.description,
                    'stream': s,
                    'captcha': chtml,
                    'admin': users.is_current_user_admin(),
                    'logout': users.create_logout_url('/'),
                    'lang': self.get_lang()
                }
                path = os.path.join(os.path.dirname(__file__), 'templates/stream.html')
                self.response.out.write( template.render(path, template_values) )
            else:
                chtml = captcha.displayhtml(
                    public_key = RECAPTCHA_PUBLIC_KEY,
                    use_ssl = False,
                    error = None)
                template_values = {
                    'title': 'Stream ' + str( s.key().id() ),
                    'description': s.description,
                    'onload': 'document.stream.password.focus()',
                    'stream': s,
                    'captcha': chtml,
                    'admin': users.is_current_user_admin(),
                    'logout': users.create_logout_url('/'),
                    'lang': self.get_lang()
                }
                path = os.path.join(os.path.dirname(__file__), 'templates/stream_ask_password.html')
                self.response.out.write( template.render(path, template_values) )
        elif ids: # stream selected but not found
            self.redirect('/error/404')
        else: # no stream selected
            self.redirect('/new')
    
    # to recive and store password
    def post(self, ids=None):
        try:
            s = Stream.get_by_id( int( ids ) )
        except:
            s = None
        
        challenge = self.request.get('recaptcha_challenge_field')
        response  = self.request.get('recaptcha_response_field')
        remoteip  = self.request.remote_addr
        cResponse = captcha.submit(challenge,
                                   response,
                                   RECAPTCHA_PRIVATE_KEY,
                                   remoteip)
        if s and self.request.get('password') == s.access_pass and cResponse.is_valid:
            # save the cookie
            c = Cookie.SimpleCookie()
            c['stream_pass_' + str( s.key().id() )] = self.request.get('password')
            c['stream_pass_' + str( s.key().id() )]['path'] = '/'
            c['stream_pass_' + str( s.key().id() )]['max-age'] = 86400
            self.response.headers.add_header('Set-Cookie', c.output())
            self.redirect( s.get_link() )
        elif s:
            self.redirect('/error/403')
        else:
            self.redirect('/error/404')
    
    def user_gives_password(self, stream):
        if self.request.cookies.get('stream_pass_' + str( stream.key().id() ), '') == stream.access_pass:
            return True
        else:
            return False


class Modify_stream(Basic_page, Basic_tools):
    def get(self, ids=None):
        try:
            s = Stream.get_by_id( int( ids ) )
        except:
            s = None
        
        if s: # stream exists
            chtml = captcha.displayhtml(
                public_key = RECAPTCHA_PUBLIC_KEY,
                use_ssl = False,
                error = None)
            template_values = {
                'title': 'Stream ' + str( s.key().id() ),
                'title2': 'Modifying stream',
                'description': s.description,
                'onload': 'document.stream.e_pass.focus()',
                'stream': s,
                'captcha': chtml,
                'admin': users.is_current_user_admin(),
                'logout': users.create_logout_url('/'),
                'lang': self.get_lang()
            }
            path = os.path.join(os.path.dirname(__file__), 'templates/modify_stream.html')
            self.response.out.write( template.render(path, template_values) )
        elif ids: # stream selected but not found
            self.redirect('/error/404')
        else: # no stream selected
            self.redirect('/new')
    
    def post(self, ids=None):
        try:
            s = Stream.get_by_id( int( ids ) )
        except:
            s = None
        if s:
            challenge = self.request.get('recaptcha_challenge_field')
            response  = self.request.get('recaptcha_response_field')
            remoteip  = self.request.remote_addr
            cResponse = captcha.submit(challenge,
                                       response,
                                       RECAPTCHA_PRIVATE_KEY,
                                       remoteip)
            if (cResponse.is_valid and self.request.get('e_pass') == s.edit_pass and s.edit_pass != '') or users.is_current_user_admin():
                try:
                    s.description = cgi.escape( self.request.get('description') )
                    # pylinks
                    if self.request.get('links'):
                        aux_links = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', self.request.get('links'))
                        s.pylinks = self.new_pylinks(aux_links, s.get_link())
                    # searches
                    if s.status in [1, 11, 91]:
                        self.tags2cache(s.tags)
                        s.tags = self.page2search(s.get_link(), s.description, 'stream', s.date)
                        s.put()
                    else:
                        s.put()
                    s.rm_cache()
                    self.redirect( s.get_link() )
                except:
                    logging.error('Cant modify stream!')
                    self.redirect('/error/500')
            else: # not allowed
                self.redirect('/error/403')
        else: # stream not found
            self.redirect('/error/404')


class Request_page(Basic_page, Basic_tools):
    def get(self, idr=None):
        try:
            r = Request.get_by_id( int( idr ) )
        except:
            r = None
        
        if r: # request exists
            chtml = captcha.displayhtml(
                public_key = RECAPTCHA_PUBLIC_KEY,
                use_ssl = False,
                error = None)
            template_values = {
                'title': 'Request ' + str( r.key().id() ),
                'description': r.description,
                'request': r,
                'comments': r.get_comments(),
                'captcha': chtml,
                'admin': users.is_current_user_admin(),
                'logout': users.create_logout_url('/'),
                'lang': self.get_lang()
            }
            path = os.path.join(os.path.dirname(__file__), 'templates/request.html')
            self.response.out.write( template.render(path, template_values) )
        elif idr: # request selected but not found
            self.redirect('/error/404')
        else: # no request selected
            self.redirect('/new')


class Modify_request(Basic_page, Basic_tools):
    def get(self, idr=None):
        try:
            r = Request.get_by_id( int( idr ) )
        except:
            r = None
        
        if r: # request exists
            chtml = captcha.displayhtml(
                public_key = RECAPTCHA_PUBLIC_KEY,
                use_ssl = False,
                error = None)
            template_values = {
                'title': 'Request ' + str( r.key().id() ),
                'title2': 'Modifying request',
                'description': r.description,
                'onload': 'document.request.e_pass.focus()',
                'request': r,
                'comments': r.get_comments(),
                'captcha': chtml,
                'admin': users.is_current_user_admin(),
                'logout': users.create_logout_url('/'),
                'lang': self.get_lang()
            }
            path = os.path.join(os.path.dirname(__file__), 'templates/modify_request.html')
            self.response.out.write( template.render(path, template_values) )
        elif idr: # request selected but not found
            self.redirect('/error/404')
        else: # no request selected
            self.redirect('/new')
    
    def post(self, idr=None):
        try:
            r = Request.get_by_id( int( idr ) )
        except:
            r = None
        if r:
            challenge = self.request.get('recaptcha_challenge_field')
            response  = self.request.get('recaptcha_response_field')
            remoteip  = self.request.remote_addr
            cResponse = captcha.submit(challenge,
                                       response,
                                       RECAPTCHA_PRIVATE_KEY,
                                       remoteip)
            if (cResponse.is_valid and self.request.get('e_pass') == r.edit_pass and r.edit_pass != '') or users.is_current_user_admin():
                try:
                    r.description = cgi.escape( self.request.get('description') )
                    # searches
                    self.tags2cache(r.tags)
                    r.tags = self.page2search(r.get_link(), r.description, 'request', r.date)
                    r.put()
                    r.rm_cache()
                    self.redirect( r.get_link() )
                except:
                    logging.error('Cant modify request!')
                    self.redirect('/error/500')
            else: # not allowed
                self.redirect('/error/403')
        else: # stream not found
            self.redirect('/error/404')


class Random_page(webapp.RequestHandler, Basic_tools):
    def get(self):
        self.pages = self.get_last_pages()
        url = '/new'
        if len( self.pages ) == 1:
            url = self.pages[0]
        elif len( self.pages ) > 1:
            url = random.choice( self.pages )
        self.redirect( url )
    
    def get_last_pages(self):
        rp = memcache.get('random_pages')
        if rp is None:
            rp = []
            ss = db.GqlQuery("SELECT * FROM Stream ORDER BY date DESC").fetch(100)
            if ss:
                for s in ss:
                    if s.status in [1, 11, 91]:
                        rp.append( s.get_link() )
            rs = db.GqlQuery("SELECT * FROM Request ORDER BY date DESC").fetch(100)
            if rs:
                for r in rs:
                    rp.append( r.get_link() )
            if len(rp) > 9:
                if not memcache.add('random_pages', rp):
                    logging.warning('Cant save random pages to memcache!')
        return rp


class Comment_to_page(webapp.RequestHandler, Basic_tools):
    # remove comment
    def get(self):
        if users.is_current_user_admin() and self.request.get('rm'):
            try:
                c = Comment.get( self.request.get('rm') )
                origin = c.get_origin()
                c.delete()
                origin.rm_cache()
                self.redirect( origin.get_link() )
            except:
                logging.error('Cant remove comment!')
                self.redirect('/error/500')
        else:
            self.redirect('/error/403')
    
    # add comment
    def post(self):
        if self.request.get('origin') and self.request.get('text'):
            challenge = self.request.get('recaptcha_challenge_field')
            response  = self.request.get('recaptcha_response_field')
            remoteip  = self.request.remote_addr
            cResponse = captcha.submit(challenge,
                                       response,
                                       RECAPTCHA_PRIVATE_KEY,
                                       remoteip)
            if cResponse.is_valid or users.is_current_user_admin():
                try:
                    c = Comment()
                    c.origin = self.request.get('origin')
                    c.text = cgi.escape( self.request.get('text') )
                    c.ip = self.request.remote_addr
                    c.os = self.request.environ['HTTP_USER_AGENT']
                    c.put()
                    origin = c.get_origin()
                    origin.rm_cache()
                    # stats
                    st = Stat_cache()
                    st.put_page('comment')
                    # tags
                    aux_tags = []
                    for tag in re.findall(r'#[0-9a-zA-Z+_]*', c.text):
                        aux_tags.append( tag[1:] )
                    self.tags2cache(aux_tags, st.get_searches())
                    # pylinks
                    aux_links = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', self.request.get('text'))
                    if aux_links:
                        # discarting images and youtube links
                        num = 0
                        while num < len(aux_links):
                            if aux_links[num][-4:].lower() in ['.jpg', '.gif', '.png']:
                                aux_links.remove( aux_links[num] )
                            elif aux_links[num][-5:].lower() in ['.jpeg']:
                                aux_links.remove( aux_links[num] )
                            elif aux_links[num][:31] == 'http://www.youtube.com/watch?v=':
                                aux_links.remove( aux_links[num] )
                            elif aux_links[num][:28] == 'http://www.xvideos.com/video':
                                aux_links.remove( aux_links[num] )
                            else:
                                num += 1
                        # storing new pylinks
                        pylinks = self.new_pylinks(aux_links, c.origin + '#' + str(c.key().id()))
                        # replacing links with pylinks
                        text = c.text
                        num = 0
                        aux_links = self.unique_links(aux_links)
                        while num < len(aux_links) and num < len(pylinks):
                            text = text.replace(aux_links[num], '[pylink]' + str(pylinks[num]) + '[/pylink]')
                            num += 1
                        c.text = text
                        c.put()
                        # stats
                        st.put_page('pylinks', len(pylinks))
                        logging.info('Encontrados ' + str(len(pylinks)) + ' pylinks!')
                    self.redirect(origin.get_link() + '#' + str(c.key().id()))
                except:
                    logging.error('Cant save comment!')
                    self.redirect('/error/500')
            else:
                self.redirect('/error/403c')
        else:
            self.redirect('/error/403')


class Report_page(Basic_page, Basic_tools):
    def get(self):
        chtml = captcha.displayhtml(
            public_key = RECAPTCHA_PUBLIC_KEY,
            use_ssl = False,
            error = None)
        template_values = {
            'title': 'Pystream: reporting',
            'title2': 'Reporting',
            'description': "Pystream's reporting page.",
            'onload': 'document.report.text.focus()',
            'link': self.request.get('link'),
            'captcha': chtml,
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/'),
            'lang': self.get_lang()
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/report.html')
        self.response.out.write( template.render(path, template_values) )
    
    def post(self):
        if self.request.get('text'):
            challenge = self.request.get('recaptcha_challenge_field')
            response  = self.request.get('recaptcha_response_field')
            remoteip  = self.request.remote_addr
            cResponse = captcha.submit(challenge,
                                       response,
                                       RECAPTCHA_PRIVATE_KEY,
                                       remoteip)
            if cResponse.is_valid:
                try:
                    r = Report()
                    if self.request.get('link') != '':
                        r.link = self.request.get('link')
                    r.text = cgi.escape( self.request.get('text') )
                    r.ip = self.request.remote_addr
                    r.os = self.request.environ['HTTP_USER_AGENT']
                    r.put()
                    self.redirect( r.get_link() )
                except:
                    logging.error('Cant save report!')
                    self.redirect('/error/500')
            else:
                self.redirect('/error/403c')
        else:
            self.redirect('/error/403')


class Search_redir(Basic_page, Basic_tools):
    def get(self):
        self.redirect('/search/' + self.request.get('query'))


class Search_page(Basic_page, Basic_tools):
    def get(self, query=None):
        query = query.replace('%20', ' ').replace('%2B', ' ')
        st = Stat_cache()
        template_values = {
            'title': 'Pystream: searching #'+query.replace(' ', '_'),
            'title2': 'Searching #'+query.replace(' ', '_'),
            'description': 'Search for #'+query.replace(' ', '_')+' on pystream.',
            'onload': 'document.search.query.focus()',
            'query': query,
            'pages': self.search( query ),
            'pylinks': self.search_pylink_file_name( query ),
            'tags': st.get_searches(),
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/'),
            'lang': self.get_lang()
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/search.html')
        self.response.out.write( template.render(path, template_values) )


class Error_page(Basic_page):
    def get(self, code='404'):
        st = Stat_cache()
        derror = {
            '403': 'Permission dennied',
            '403c': 'Captcha fail',
            '404': 'Page not found',
            '500': 'Internal server error',
        }
        template_values = {
            'title': str(code) + ' - pystream',
            'title2': 'Anonymous community',
            'description': derror.get(code, 'Unknown error'),
            'onload': 'document.search.query.focus()',
            'code': code,
            'tags': st.get_searches(),
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/'),
            'lang': self.get_lang()
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/search.html')
        self.response.out.write(template.render(path, template_values))


def main():
    application = webapp.WSGIApplication([('/', Main_page),
                                          ('/new', New_page),
                                          ('/new_links', New_stream_page),
                                          ('/new_request', New_request_page),
                                          ('/download', Download_page),
                                          (r'/s/(.*)', Stream_page),
                                          (r'/ps/(.*)', Protected_stream_page),
                                          (r'/r/(.*)', Request_page),
                                          ('/mod_stream/(.*)', Modify_stream),
                                          ('/mod_request/(.*)', Modify_request),
                                          ('/random', Random_page),
                                          ('/comment', Comment_to_page),
                                          ('/report', Report_page),
                                          ('/search', Search_redir),
                                          (r'/search/(.*)', Search_page),
                                          (r'/error/(.*)', Error_page),
                                          ('/.*', Error_page)],
                                         debug=DEBUG_FLAG)
    webapp.template.register_template_library('filters.django_filters')
    run_wsgi_app(application)


if __name__ == "__main__":
    main()

