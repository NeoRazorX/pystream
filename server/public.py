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

import cgi, os, random, Cookie, math

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
        template_values = {
            'title': 'pystream',
            'description': 'Sharing folders made easy.',
            'user_os': self.get_os( self.request.environ['HTTP_USER_AGENT'] ),
            'windows_client_url': WINDOWS_CLIENT_URL,
            'linux_client_url': LINUX_CLIENT_URL,
            'mac_client_url': MAC_CLIENT_URL,
            'local_streams': self.near_streams(),
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/'),
            'lang': self.get_lang()
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
        self.response.out.write( template.render(path, template_values) )
    
    def near_streams(self):
        return self.order_streams_date( self.get_streams_from_ip( self.request.remote_addr ) )


class Stream_page(Basic_page, Basic_tools):
    def get(self, ids=None):
        try:
            s = Stream.get_by_id( int( ids ) )
        except:
            s = None
        
        if s: # stream exists
            if s.password != '': # is password protected
                # must use /sp/ folder
                self.redirect('/sp/' + str( s.key().id() ) )
            if self.request.get('key') == str( s.key() ): # give us the key?
                if not self.is_publisher( s.key() ): # have cookie?
                    # save the cookie
                    c = Cookie.SimpleCookie()
                    c['key' + str( s.key().id() )] = self.request.get('key')
                    c['key' + str( s.key().id() )]['path'] = '/'
                    c['key' + str( s.key().id() )]['max-age'] = 86400
                    self.response.headers.add_header('Set-Cookie', c.output())
                # we dont want the user to post the key by mistake,
                # so we reload without key on url
                self.redirect( s.get_link() )
            else: # all correct
                chtml = captcha.displayhtml(
                    public_key = RECAPTCHA_PUBLIC_KEY,
                    use_ssl = False,
                    error = None)
                template_values = {
                    'title': 'pystream: ' + str( s.key().id() ),
                    'description': s.description,
                    'stream': s,
                    'comments': s.get_comments(),
                    'captcha': chtml,
                    'admin': users.is_current_user_admin(),
                    'logout': users.create_logout_url('/'),
                    'publisher': self.is_publisher( s.key() ),
                    'lang': self.get_lang()
                }
                path = os.path.join(os.path.dirname(__file__), 'templates/stream.html')
                self.response.out.write( template.render(path, template_values) )
        elif ids: # stream selected but not found
            self.redirect('/error/404')
        else: # no stream selected
            # new stream page
            template_values = {
                'title': 'pystream: new stream',
                'description': 'Sharing folders made easy.',
                'pystream_version': PYSTREAM_VERSION,
                'admin': users.is_current_user_admin(),
                'logout': users.create_logout_url('/'),
                'user_os': self.get_os( self.request.environ['HTTP_USER_AGENT'] ),
                'lang': self.get_lang(),
                'windows_client_url': WINDOWS_CLIENT_URL,
                'linux_client_url': LINUX_CLIENT_URL,
                'mac_client_url': MAC_CLIENT_URL
            }
            path = os.path.join(os.path.dirname(__file__), 'templates/new.html')
            self.response.out.write( template.render(path, template_values) )
    
    # add new stream
    def post(self):
        if self.request.get('version') != PYSTREAM_VERSION: # bad client version
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write('Bad version! You need to download a new client -> http://www.pystream.com/new')
            logging.warning('Bad client version!')
        elif self.request.get('web') and self.request.get('ip') and self.request.get('port'): # webclient request
            try:
                s = Stream()
                s.ip = self.dottedQuadToNum( self.request.get('ip') )
                s.port = int( self.request.get('port') )
                s.lan_ip = s.ip
                s.os = "web"
                if s.new_stream():
                    self.redirect('/s/' + str( s.key().id() ) + '?key=' + str( s.key() ))
                else:
                    self.redirect('/error/403')
            except:
                logging.error('Fail to store stream from web -> ' + self.request.get('ip') + ':' + self.request.get('port'))
                self.redirect('/error/500')
        else: # lost parameters
            self.redirect('/error/403')
    
    def is_publisher(self, key):
        if self.request.cookies.get('key' + str( key.id() ), '') == str(key):
            return True
        else:
            return False


class Stream_protected_page(Stream_page, Basic_tools):
    def get(self, ids=None):
        try:
            s = Stream.get_by_id( int( ids ) )
        except:
            s = None
        
        if s: # stream exists
            if s.password == '': # is password protected
                # must use /s/ folder
                self.redirect('/s/' + str( s.key().id() ) )
            elif not users.is_current_user_admin() and not self.is_publisher( s.key() ) and not self.user_give_password(s):
                # captcha
                chtml = captcha.displayhtml(
                    public_key = RECAPTCHA_PUBLIC_KEY,
                    use_ssl = False,
                    error = None)
                template_values = {
                    'title': 'pystream: ' + str( s.key().id() ),
                    'description': 'Sharing folders made easy.',
                    'streamid': s.key().id(),
                    'captcha': chtml,
                    'admin': users.is_current_user_admin(),
                    'logout': users.create_logout_url('/'),
                    'lang': self.get_lang()
                }
                path = os.path.join(os.path.dirname(__file__), 'templates/stream_ask_password.html')
                self.response.out.write( template.render(path, template_values) )
            else: # all correct, show full stream
                # captcha
                chtml = captcha.displayhtml(
                    public_key = RECAPTCHA_PUBLIC_KEY,
                    use_ssl = False,
                    error = None)
                template_values = {
                    'title': 'pystream: ' + str( s.key().id() ),
                    'description': s.description,
                    'stream': s,
                    'comments': s.get_comments(),
                    'captcha': chtml,
                    'admin': users.is_current_user_admin(),
                    'logout': users.create_logout_url('/'),
                    'publisher': self.is_publisher( s.key() ),
                    'lang': self.get_lang()
                }
                path = os.path.join(os.path.dirname(__file__), 'templates/stream.html')
                self.response.out.write( template.render(path, template_values) )
        else: # stream not found
            self.redirect('/error/404')
    
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
        if s and self.request.get('password') == s.password and cResponse.is_valid:
            # save the cookie
            c = Cookie.SimpleCookie()
            c['pass' + str( s.key().id() )] = self.request.get('password')
            c['pass' + str( s.key().id() )]['path'] = '/'
            c['pass' + str( s.key().id() )]['max-age'] = 86400
            self.response.headers.add_header('Set-Cookie', c.output())
            self.redirect('/sp/' + str( s.key().id() ))
        elif s:
            self.redirect('/error/403')
        else:
            self.redirect('/error/404')
    
    def user_give_password(self, stream):
        if self.request.cookies.get('pass' + str( stream.key().id() ), '') == stream.password:
            return True
        else:
            return False


class Modify_stream(Stream_page):
    def get(self):
        self.redirect('/error/403')
    
    def post(self):
        try:
            s = Stream.get( self.request.get('key') )
        except:
            s = None
        if s:
            if users.is_current_user_admin() or self.is_publisher( s.key() ):
                try:
                    s.description = cgi.escape( self.request.get('description').replace("\n", ' ') )[:499]
                    s.password = cgi.escape( self.request.get('password') )
                    if s.password:
                        s.public = False
                        s.online = False
                    elif self.request.get('public') == 'False':
                        s.public = False
                        s.online = False
                    else:
                        s.public = True
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


class Random_stream(webapp.RequestHandler):
    def get(self):
        self.streams = self.get_last_streams()
        url = '/new'
        if len( self.streams ) == 1:
            url = '/s/' + str( self.streams[0].key().id() )
        elif len( self.streams ) > 1:
            url = '/s/' + str( random.choice( self.streams ).key().id() )
        self.redirect( url )
    
    def get_last_streams(self):
        ss = memcache.get('random_streams')
        if ss is None:
            ss = db.GqlQuery("SELECT * FROM Stream WHERE online = :1", True).fetch(100)
            if not memcache.add('random_streams', ss):
                logging.warning('Cant save random streams to memcache!')
        return ss


class Comment_stream(webapp.RequestHandler, Basic_tools):
    # remove comment
    def get(self):
        if users.is_current_user_admin() and self.request.get('rm'):
            try:
                c = Comment.get( self.request.get('rm') )
                s = c.get_stream()
                c.delete()
                s.rm_cache()
                self.redirect( s.get_link() )
            except:
                logging.error('Cant remove comment!')
                self.redirect('/error/500')
        else:
            self.redirect('/error/403')
    
    # add comment
    def post(self):
        if self.request.get('stream_id') and self.request.get('text'):
            challenge = self.request.get('recaptcha_challenge_field')
            response  = self.request.get('recaptcha_response_field')
            remoteip  = self.request.remote_addr
            cResponse = captcha.submit(challenge,
                                       response,
                                       RECAPTCHA_PRIVATE_KEY,
                                       remoteip)
            if cResponse.is_valid:
                try:
                    s = Stream.get_by_id( int( self.request.get('stream_id') ) )
                    c = Comment()
                    c.stream_id = int( self.request.get('stream_id') )
                    c.text = cgi.escape( self.request.get('text') )
                    c.ip = self.dottedQuadToNum( self.request.remote_addr )
                    c.os = self.request.environ['HTTP_USER_AGENT']
                    if self.is_publisher( s.key() ):
                        c.autor = 'publisher'
                    elif users.is_current_user_admin():
                        c.autor = 'admin'
                    c.put()
                    s.rm_cache()
                    self.redirect( s.get_link() )
                except:
                    logging.error('Cant save comment!')
                    self.redirect('/error/500')
            else:
                self.redirect('/error/403c')
        else:
            self.redirect('/error/403')
    
    def is_publisher(self, key):
        if self.request.cookies.get('key' + str( key.id() ), '') == str(key):
            return True
        else:
            return False


class Report_page(Basic_page, Basic_tools):
    def get(self):
        chtml = captcha.displayhtml(
            public_key = RECAPTCHA_PUBLIC_KEY,
            use_ssl = False,
            error = None)
        template_values = {
            'title': 'pystream: reporting',
            'description': "Pystream's reporting page.",
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
                    r.link = self.request.get('link')
                    r.text = cgi.escape( self.request.get('text') )
                    r.ip = self.dottedQuadToNum( self.request.remote_addr )
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


class Search_page(Basic_page, Basic_tools):
    def get(self):
        template_values = {
            'title': 'pystream: searching',
            'description': 'Search for public streams and private streams from your LAN.',
            'onload': 'document.search.query.focus()',
            'query': self.request.get('query'),
            'streams': self.search_streams( self.request.get('query') ),
            'previouss': self.previous_searches( self.request.get('query') ),
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/'),
            'lang': self.get_lang()
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/search.html')
        self.response.out.write( template.render(path, template_values) )
    
    def search_streams(self, query):
        if query:
            mix = []
            ss = Stream.all().search( query ).fetch(100)
            # filtering for online or private near streams
            for s in ss:
                if s.online or s.ip == self.dottedQuadToNum(self.request.remote_addr):
                    mix.append( s )
            return self.order_streams_date(mix)
        else:
            return None
    
    def previous_searches(self, query):
        schs = memcache.get('previous_searches')
        if query:
            found = False
            if schs is None:
                schs = [[query, 1]]
                memcache.add('previous_searches', schs)
            else:
                for s in schs:
                    if s[0] == query:
                        s[1] += 1
                        found = True
                # short and limit to 19
                if schs:
                    total = 0
                    aux = []
                    elem = None
                    while schs != []:
                        for s in schs:
                            if not elem:
                                elem = s
                            elif s[1] > elem[1]:
                                elem = s
                        if total < 19:
                            aux.append(elem)
                            total += 1
                        schs.remove(elem)
                        elem = None
                    schs = aux
                if not found:
                    schs.append([query, 1])
                memcache.replace('previous_searches', schs)
        return schs


class Author_page(Basic_page):
    def get(self):
        template_values = {
            'title': 'pystream: author',
            'description': "Information about Carlos Garcia Gomez, pystream's author",
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/'),
            'lang': self.get_lang()
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/author.html')
        self.response.out.write( template.render(path, template_values) )


class Error_page(Basic_page):
    def get(self, code='404'):
        derror = {
            '403': 'Permission dennied',
            '403c': 'Captcha fail',
            '404': 'Page not found',
            '500': 'Internal server error',
        }
        
        template_values = {
            'title': str(code) + ' - pystream',
            'description': derror.get(code, 'Unknown error'),
            'code': code,
            'previouss': memcache.get('previous_searches'),
            'lang': self.get_lang()
            }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/search.html')
        self.response.out.write(template.render(path, template_values))

def main():
    application = webapp.WSGIApplication([('/', Main_page),
                                          ('/new', Stream_page),
                                          (r'/s/(.*)', Stream_page),
                                          (r'/sp/(.*)', Stream_protected_page),
                                          ('/mod_stream', Modify_stream),
                                          ('/random', Random_stream),
                                          ('/comment', Comment_stream),
                                          ('/report', Report_page),
                                          ('/search', Search_page),
                                          ('/author', Author_page),
                                          (r'/error/(.*)', Error_page),
                                          ('/.*', Error_page)],
                                         debug=DEBUG_FLAG)
    webapp.template.register_template_library('filters.django_filters')
    run_wsgi_app(application)


if __name__ == "__main__":
    main()

