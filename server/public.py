#!/usr/bin/env python

import cgi, os, logging, random, Cookie

# cargamos django 1.2
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')
from google.appengine.ext.webapp import template

from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from recaptcha.client import captcha
from base import *

class Main_page(webapp.RequestHandler):
    def get(self):
        template_values = {
            'title': 'pyStream (alpha)',
            'description': 'Data sharing made easy.',
            'tags': 'share, folder, python, linux, ubuntu',
            'admin': users.is_current_user_admin()
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
        self.response.out.write( template.render(path, template_values) )

class Stream_page(webapp.RequestHandler):
    def get(self, ids=None):
        try:
            s = Stream.get_by_id( int( ids ) )
        except:
            s = None
        
        if s: # show stream
            # is publisher? save the cookie
            if self.request.get('key') == str( s.key() ) and not self.is_publisher( s.key() ):
                c = Cookie.SimpleCookie()
                c['key' + str( s.key().id() )] = self.request.get('key')
                c['key' + str( s.key().id() )]['path'] = '/'
                c['key' + str( s.key().id() )]['max-age'] = 86400
                self.response.headers.add_header('Set-Cookie', c.output())
                self.redirect('/s/' + str( s.key().id() ))
            else:
                # captcha
                chtml = captcha.displayhtml(
                    public_key = RECAPTCHA_PUBLIC_KEY,
                    use_ssl = False,
                    error = None)
                template_values = {
                    'title': 'pyStream (alpha) ' + str( s.key().id() ),
                    'description': 'Data sharing made easy.',
                    'tags': 'share, folder, python, linux, ubuntu',
                    'stream': s,
                    'local': self.from_local( self.numToDottedQuad( s.ip ) ),
                    'comments': s.get_comments(),
                    'captcha': chtml,
                    'admin': users.is_current_user_admin(),
                    'publisher': self.is_publisher( s.key() )
                }
                path = os.path.join(os.path.dirname(__file__), 'templates/stream.html')
                self.response.out.write( template.render(path, template_values) )
        elif ids: # stream selected but not found
            self.redirect('/error/404')
        else: # new stream page
            # want to remove stream? must be admin
            if self.request.get('rm') and users.is_current_user_admin():
                try:
                    s = Stream.get( self.request.get('rm') )
                    s.rm_comments()
                    s.rm_cache()
                    s.delete()
                    self.redirect('/admin/')
                except:
                    logging.warning('Fail to remove stream!')
                    self.redirect('/error/503')
            else:
                template_values = {
                    'title': 'pyStream (alpha)',
                    'description': 'Data sharing made easy.',
                    'tags': 'share, folder, python, linux, ubuntu'
                }
                path = os.path.join(os.path.dirname(__file__), 'templates/new.html')
                self.response.out.write( template.render(path, template_values) )
    
    # add new stream
    def post(self):
        if self.request.get('ip') and self.request.get('port'):
            ok = False
            try:
                s = Stream()
                s.ip = self.dottedQuadToNum( self.request.get('ip') )
                s.port = int( self.request.get('port') )
                s.put()
                ok = True
            except:
                logging.warning('Fail to store stream -> ' + self.request.get('ip') + ':' + self.request.get('port'))
            if ok:
                self.response.out.write('key: ' + str( s.key() ) + ';id: ' + str( s.key().id() ) )
            else:
                self.error(500)
        else:
            self.error(403)
    
    def dottedQuadToNum(self, ip):
        hexn = ''.join(["%02X" % long(i) for i in ip.split('.')])
        return long(hexn, 16)
    
    def numToDottedQuad(self, n):
        d = 256 * 256 * 256
        q = []
        while d > 0:
            m,n = divmod(n,d)
            q.append(str(m))
            d = d/256
        return '.'.join(q)
    
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

class Random_stream(webapp.RequestHandler):
    def get(self):
        s = self.select_random()
        if s:
            self.redirect('/s/' + str( s.key().id() ))
        else:
            self.redirect('/new')
    
    def select_random(self):
        ss = db.GqlQuery("SELECT * FROM Stream ORDER BY date DESC").fetch(20)
        if not ss:
            return None
        elif len(ss) == 1:
            return ss[0]
        else:
            return ss[random.randint(0, len(ss)-1)]

class Comment_stream(webapp.RequestHandler):
    # remove comment
    def get(self):
        if users.is_current_user_admin() and self.request.get('idc'):
            try:
                c = Comment.get_by_id( int( self.request.get('idc') ) )
                c.delete()
                self.redirect( self.check_link( c.link ) )
            except:
                logging.warning('Cant remove comment!')
                self.redirect('/error/503')
        else:
            self.redirect('/error/403')
    
    # add comment
    def post(self):
        if self.request.get('link') and self.request.get('text'):
            c = Comment()
            c.link = self.request.get('link')
            c.text = cgi.escape( self.request.get('text') )
            c.ip = self.dottedQuadToNum( self.request.remote_addr )
            url,publisher = self.check_link( c.link )
            if users.is_current_user_admin():
                c.autor = 'admin'
            elif publisher:
                c.autor = 'publisher'
            challenge = self.request.get('recaptcha_challenge_field')
            response  = self.request.get('recaptcha_response_field')
            remoteip  = self.request.remote_addr
            cResponse = captcha.submit(challenge,
                                       response,
                                       RECAPTCHA_PRIVATE_KEY,
                                       remoteip)
            if cResponse.is_valid:
                try:
                    c.put()
                    self.redirect( url )
                except:
                    logging.warning('Cant save comment!')
                    self.redirect('/error/503')
            else:
                self.redirect('/error/403c')
        else:
            self.redirect('/error/403')
    
    def dottedQuadToNum(self, ip):
        hexn = ''.join(["%02X" % long(i) for i in ip.split('.')])
        return long(hexn, 16)
    
    def check_link(self, link):
        url = '/'
        publisher = False
        if link[:23] == 'http://www.pystream.com':
            url = link.replace('http://www.pystream.com', '')
            if url[:3] == '/s/':
                try:
                    s = Stream.get_by_id( int( url[3:] ) )
                    if self.request.cookies.get('key' + str( s.key().id() ),'') == str( s.key() ):
                        publisher = True
                    s.rm_cache()
                except:
                    logging.error('Cant get stream!')
        return url,publisher

def main():
    application = webapp.WSGIApplication([('/', Main_page),
                                         ('/new', Stream_page),
                                         (r'/s/(.*)', Stream_page),
                                         ('/random', Random_stream),
                                         ('/comment', Comment_stream),
                                         ],
                                         debug=DEBUG_FLAG)
    webapp.template.register_template_library('filters.django_filters')
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

