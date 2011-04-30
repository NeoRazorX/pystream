#!/usr/bin/env python

import cgi, os, random, Cookie

# cargamos django 1.2
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')
from google.appengine.ext.webapp import template

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from recaptcha.client import captcha
from base import *


class Main_page(webapp.RequestHandler, ip_item):
    def get(self):
        template_values = {
            'title': 'pyStream (alpha)',
            'description': 'Data sharing made easy.',
            'tags': 'share, folder, python, linux, ubuntu',
            'onload': 'document.search.query.focus()',
            'local_streams': self.get_local_streams(),
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/')
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
        self.response.out.write( template.render(path, template_values) )
    
    def get_local_streams(self):
        ss = db.GqlQuery("SELECT * FROM Stream WHERE ip = :1",
                         self.dottedQuadToNum( self.request.remote_addr ) ).fetch(20)
        return ss


class Stream_page(webapp.RequestHandler, ip_item):
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
                    'title': 'pyStream (alpha) ' + str( s.key().id() ),
                    'description': s.description,
                    'tags': 'share, folder, python, linux, ubuntu',
                    'stream': s,
                    'local': self.from_local( self.numToDottedQuad( s.ip ) ),
                    'comments': s.get_comments(),
                    'captcha': chtml,
                    'admin': users.is_current_user_admin(),
                    'logout': users.create_logout_url('/'),
                    'publisher': self.is_publisher( s.key() )
                }
                path = os.path.join(os.path.dirname(__file__), 'templates/stream.html')
                self.response.out.write( template.render(path, template_values) )
        elif ids: # stream selected but not found
            self.redirect('/error/404')
        else: # no stream selected
            # new stream page
            template_values = {
                'title': 'pyStream (alpha) - new stream',
                'description': 'Data sharing made easy.',
                'tags': 'share, folder, python, linux, ubuntu',
                'pystream_version': PYSTREAM_VERSION,
                'admin': users.is_current_user_admin(),
                'logout': users.create_logout_url('/')
            }
            path = os.path.join(os.path.dirname(__file__), 'templates/new.html')
            self.response.out.write( template.render(path, template_values) )
    
    # add new stream
    def post(self):
        if self.request.get('version') != PYSTREAM_VERSION: # bad client version
            self.response.out.write('Bad version! You need to download a new client -> http://www.pystream.com/new')
            logging.warning('Bad client version!')
        elif self.request.get('web') and self.request.get('ip') and self.request.get('port'): # webclient request
            ok = False
            try:
                s = Stream()
                s.ip = self.dottedQuadToNum( self.request.get('ip') )
                s.port = int( self.request.get('port') )
                if self.request.get('lan_ip'):
                    s.lan_ip = self.dottedQuadToNum( self.request.get('lan_ip') )
                else:
                    s.lan_ip = s.ip
                s.put()
                ok = True
            except:
                logging.error('Fail to store stream -> ' + self.request.get('ip') + ':' + self.request.get('port'))
            if ok:
                self.redirect('/s/' + str( s.key().id() ) + '?key=' + str( s.key() ))
            else:
                self.error(500)
        elif self.request.get('port') and (self.request.get('ip') or self.request.get('lan_ip')): # client request
            ok = False
            try:
                s = Stream()
                if self.request.get('ip'):
                    s.ip = self.dottedQuadToNum( self.request.get('ip') )
                else:
                    s.ip = self.dottedQuadToNum( self.request.remote_addr )
                s.port = int( self.request.get('port') )
                if self.request.get('lan_ip'):
                    s.lan_ip = self.dottedQuadToNum( self.request.get('lan_ip') )
                else:
                    s.lan_ip = s.ip
                if self.request.get('description'):
                    s.description = cgi.escape( self.request.get('description').replace("\n", ' ') )[:499]
                if self.request.get('size'):
                    s.size = int( self.request.get('size') )
                if self.request.get('os'):
                    s.os = cgi.escape( self.request.get('os') )
                if self.request.get('public') == 'False':
                    s.public = False
                s.put()
                ok = True
            except:
                logging.error('Fail to store stream -> ' + self.request.get('ip') + ':' + self.request.get('port'))
            if ok:
                s.rm_cache()
                self.response.out.write('key: ' + str( s.key() ) + ';id: ' + str( s.key().id() ) )
            else:
                self.error(403)
        else: # lost parameters
            self.error(403)
    
    def from_local(self, ip):
        if ip == self.request.remote_addr:
            return True
        elif self.request.remote_addr == '127.0.0.1':
            return True
        else:
            return False
    
    def is_publisher(self, key):
        if self.request.cookies.get('key' + str( key.id() ), '') == str(key):
            return True
        else:
            return False


class Stream_protected_page(Stream_page):
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
                    'title': 'pyStream (alpha) ' + str( s.key().id() ),
                    'description': 'Data sharing made easy.',
                    'tags': 'share, folder, python, linux, ubuntu',
                    'streamid': s.key().id(),
                    'captcha': chtml,
                    'admin': users.is_current_user_admin(),
                    'logout': users.create_logout_url('/')
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
                    'title': 'pyStream (alpha) ' + str( s.key().id() ),
                    'description': s.description,
                    'tags': 'share, folder, python, linux, ubuntu',
                    'stream': s,
                    'local': self.from_local( self.numToDottedQuad( s.ip ) ),
                    'comments': s.get_comments(),
                    'captcha': chtml,
                    'admin': users.is_current_user_admin(),
                    'logout': users.create_logout_url('/'),
                    'publisher': self.is_publisher( s.key() )
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
            url = '/s/' + str( self.streams[ random.randint(0, len( self.streams )-1) ].key().id() )
        self.redirect( url )
    
    def get_last_streams(self):
        ss = memcache.get('random_streams')
        if ss is None:
            ss = db.GqlQuery("SELECT * FROM Stream WHERE online = :1 ORDER BY date DESC",
                             True).fetch(100)
            if not memcache.add('random_streams', ss):
                logging.warning('Cant save random streams to memcache!')
        return ss


class Comment_stream(webapp.RequestHandler, ip_item):
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
                    if users.is_current_user_admin():
                        c.autor = 'admin'
                    elif self.is_publisher( s.key() ):
                        c.autor = 'publisher'
                    c.put()
                    s.rm_cache()
                    self.redirect( s.get_link() )
                except:
                    logging.error('Cant save comment!')
                    self.redirect('/error/500')
            else:
                self.redirect('/error/403')
        else:
            self.redirect('/error/403')
    
    def is_publisher(self, key):
        if self.request.cookies.get('key' + str( key.id() ), '') == str(key):
            return True
        else:
            return False


class Report_page(webapp.RequestHandler, ip_item):
    def get(self):
        chtml = captcha.displayhtml(
            public_key = RECAPTCHA_PUBLIC_KEY,
            use_ssl = False,
            error = None)
        template_values = {
            'title': 'pyStream (alpha) - reporting',
            'description': 'Report page',
            'tags': 'share, folder, python, linux, ubuntu',
            'link': self.request.get('link'),
            'captcha': chtml,
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/')
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/report.html')
        self.response.out.write( template.render(path, template_values) )
    
    def post(self):
        if self.request.get('link') and self.request.get('text'):
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
                self.redirect('/error/403')
        else:
            self.redirect('/error/403')


class Search_page(webapp.RequestHandler, ip_item):
    def get(self):
        template_values = {
            'title': 'pyStream (alpha) - searching',
            'description': 'Data sharing made easy.',
            'tags': 'share, folder, python, linux, ubuntu',
            'onload': 'document.search.query.focus()',
            'query': self.request.get('query'),
            'streams': self.search_streams( self.request.get('query') ),
            'admin': users.is_current_user_admin(),
            'logout': users.create_logout_url('/')
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/search.html')
        self.response.out.write( template.render(path, template_values) )
    
    def search_streams(self, query):
        if query:
            ss = Stream.all().filter('online = ', True).search( query ).fetch(20)
            return ss
        else:
            return None


class Error_page(webapp.RequestHandler):
    def get(self, code='404'):
        derror = {
            '403': 'Permission dennied',
            '404': 'Page not found',
            '500': 'Internal error',
        }
        
        merror = {
            '403': '403 - Permission dennied',
            '404': '404 - Page not found',
            '500': '500 - Internal error, check state on: http://code.google.com/status/appengine',
        }
        
        template_values = {
            'title': str(code) + ' - pystream',
            'description': derror.get(code, 'Unknown error'),
            'error': merror.get(code, 'Unknown error')
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
                                         ('/error/(.*)', Error_page),
                                         ('/.*', Error_page),
                                         ],
                                         debug=DEBUG_FLAG)
    webapp.template.register_template_library('filters.django_filters')
    run_wsgi_app(application)


if __name__ == "__main__":
    main()

