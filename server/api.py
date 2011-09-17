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

import cgi, os, random, math, datetime, re
from google.appengine.api import users
from google.appengine.ext.webapp.util import run_wsgi_app
from base import *

class Hello(webapp.RequestHandler, Basic_tools):
    def get(self):
        self.error(403)
    
    def post(self):
        if self.request.get('version') != PYSTREAM_VERSION: # bad client version
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write("Bad version!\nYou need to download a new client -> http://www.pystream.com/download")
            logging.info('Bad client version! v'+self.request.get('version'))
        elif self.request.get('machine'):
            logging.info('Machine: ' + self.request.get('machine'))
            st = Stat_cache()
            st.put_machine(self.request.get('machine'), self.is_ip6(self.request.remote_addr), self.request.get('upnp'))
        else:
            self.error(403)

class New_stream(webapp.RequestHandler, Basic_tools):
    def get(self):
        self.error(403)
    
    def post(self):
        if self.request.get('version') != PYSTREAM_VERSION: # bad client version
            logging.info('Bad client version! v'+self.request.get('version'))
            self.error(403)
        elif self.request.get('machine') and self.request.get('port') and self.request.get('links'):
            try:
                s = Stream()
                if self.request.get('description'):
                    s.description = cgi.escape( self.request.get('description') )
                else:
                    if len(self.request.get('links')) > 200:
                        s.description = 'Sharing files: ' + cgi.escape( self.request.get('links')[:200].replace("\n", ' ') ) + '...'
                    else:
                        s.description = 'Sharing files: ' + cgi.escape( self.request.get('links').replace("\n", ' ') )
                s.ip = self.request.remote_addr
                try:
                    s.port = int( self.request.get('port') )
                except:
                    logging.error('Invalid port!')
                if self.request.get('lan_ip') not in ['', self.request.remote_addr]:
                    s.lan_ip = self.request.get('lan_ip')
                s.os = self.request.get('machine')
                try:
                    s.size = int(self.request.get('size'))
                except:
                    s.size = 0
                # edition password
                s.edit_pass = str( random.randint(0, 999999) )
                # stream status
                if self.is_ip6(self.request.remote_addr):
                    if self.request.get('public') == 'True':
                        s.status = 1
                    elif self.request.get('a_pass'):
                        s.access_pass = self.request.get('a_pass')
                        s.status = 3
                    else:
                        s.status = 2
                else:
                    if self.request.get('public') == 'True':
                        s.status = 11
                    elif self.request.get('a_pass'):
                        s.access_pass = self.request.get('a_pass')
                        s.status = 13
                    else:
                        s.status = 12
                s.put()
                # pylinks
                if self.request.get('links'):
                    links = []
                    for link in self.request.get('links').splitlines():
                        links.append('/api/redir/' + str( s.key().id() ) + link)
                    s.pylinks = self.new_pylinks(links, s.get_link())
                    s.put()
                # searches
                s.tags = self.page2search(s.get_link(), s.description, 'stream', s.date)
                s.put()
                # stats
                st = Stat_cache()
                st.put_page('stream')
                st.put_page('pylinks', len(s.pylinks))
                # response
                self.response.headers['Content-Type'] = 'text/plain'
                self.response.out.write( str(s.key()) + "\n" + s.get_link() + "\n" + s.edit_pass )
            except:
                logging.error('Fail to store stream -> ' + self.request.get('machine'))
                self.error(500)
        else: # lost parameters
            self.error(403)


class Stream_alive(webapp.RequestHandler, Basic_tools):
    def get(self):
        self.error(403)
    
    def post(self):
        if self.request.get('version') != PYSTREAM_VERSION: # bad client version
            logging.info('Bad client version! v'+self.request.get('version'))
            self.error(403)
        elif self.request.get('key'):
            try:
                s = Stream.get( self.request.get('key') )
                s.alive = datetime.datetime.now()
                s.put()
            except:
                logging.error('Fail to set stream alive -> ' + self.request.get('key'))
                self.error(500)
        else:
            self.error(403)


class Close_stream(webapp.RequestHandler, Basic_tools):
    def get(self):
        self.error(403)
    
    def post(self):
        if self.request.get('version') != PYSTREAM_VERSION: # bad client version
            logging.info('Bad client version! v'+self.request.get('version'))
            self.error(403)
        elif self.request.get('key'):
            try:
                s = Stream.get( self.request.get('key') )
                s.status = 100
                s.password = ''
                s.put()
                # pylinks
                for pyl in s.get_pylinks():
                    if pyl.origin == [ s.get_link() ]:
                        db.delete( pyl.key() )
            except:
                logging.error('Fail to close stream -> ' + self.request.get('key'))
                self.error(500)
        else: # lost parameters
            self.error(403)


class Redir_link(webapp.RequestHandler, Basic_tools):
    def get(self, ids=None, link=None):
        if ids and link:
            try:
                s = Stream.get_by_id( int(ids) )
                if s:
                    if s.ip == self.request.remote_addr:
                        if self.is_ip6(self.request.remote_addr):
                            self.redirect('http://localhost:' + str(s.port) + '/' + link)
                        elif s.lan_ip:
                            self.redirect('http://' + s.lan_ip + ':' + str(s.port) + '/' + link)
                        else:
                            self.redirect('http://' + s.ip + ':' + str(s.port) + '/' + link)
                    else:
                        self.redirect('http://' + s.ip + ':' + str(s.port) + '/' + link)
                else:
                    self.error(404)
            except:
                logging.warning("Can't redir on stream: " + ids + " to: " + link)
                self.error(500)
        else:
            self.error(403)


def main():
    application = webapp.WSGIApplication([('/api/hello', Hello),
                                          ('/api/new', New_stream),
                                          ('/api/alive', Stream_alive),
                                          ('/api/close', Close_stream),
                                          (r'/api/redir/(.*)/(.*)', Redir_link)],
                                         debug=DEBUG_FLAG)
    run_wsgi_app(application)


if __name__ == "__main__":
    main()

