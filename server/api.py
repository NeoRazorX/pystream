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
        elif self.request.get('machine'):
            try:
                st = Stat_cache()
                s = Stream()
                if self.request.get('description'):
                    s.description = cgi.escape( self.request.get('description') )
                else:
                    if len(self.request.get('links')) > 449:
                        s.description = 'Sharing files: ' + cgi.escape( self.request.get('links')[:449].replace("\n", ' ') ) + '...'
                    elif self.request.get('links'):
                        s.description = 'Sharing files: ' + cgi.escape( self.request.get('links').replace("\n", ' ') )
                    else:
                        s.description = 'No description :('
                s.ip = self.request.remote_addr
                s.os = self.request.get('machine')
                # is a fake stream?
                if self.request.get('fake') == 'True':
                    if self.request.get('public') == 'True':
                        s.status = 91
                    elif self.request.get('a_pass'):
                        s.access_pass = self.request.get('a_pass')
                        s.status = 93
                    else:
                        s.status = 92
                else: # non fake stream
                    try:
                        s.port = int( self.request.get('port') )
                    except:
                        s.port = 8081
                    if self.request.get('lan_ip') not in ['', self.request.remote_addr]:
                        s.lan_ip = self.request.get('lan_ip')
                    try:
                        s.size = int(self.request.get('size'))
                    except:
                        s.size = 0
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
                # edition password
                s.edit_pass = self.get_random_password()
                s.put()
                # pylinks
                if self.request.get('links'):
                    links = []
                    for link in self.request.get('links').splitlines():
                        if link[0] == '/':
                            links.append('/api/redir/' + str(s.key().id()) + link)
                        else:
                            links.append(link)
                    s.pylinks = self.new_pylinks(links, s.get_link())
                    s.put()
                # searches
                s.tags = self.page2search(s.get_link(), s.description, 'stream', s.date)
                s.put()
                # stats
                if self.request.get('firewalled') == 'True':
                    st.put_firewalled_machine(self.request.get('machine'))
                st.put_page('stream')
                st.put_page('pylinks', len(s.pylinks))
                # response
                self.response.headers['Content-Type'] = 'text/plain'
                self.response.out.write( str(s.key()) + "\n" + s.get_link() + "\n" + s.edit_pass + "\n" + self.request.remote_addr)
            except:
                logging.error('Fail to store stream -> ' + self.request.get('machine'))
                self.error(500)
        else: # lost parameters
            self.error(403)


class Stream_add_link(webapp.RequestHandler, Basic_tools):
    def get(self):
        self.error(403)
    
    def post(self):
        if self.request.get('version') != PYSTREAM_VERSION: # bad client version
            logging.info('Bad client version! v'+self.request.get('version'))
            self.error(403)
        elif self.request.get('key') and self.request.get('links'):
            try:
                s = Stream.get( self.request.get('key') )
                try:
                    s.size = int(self.request.get('size'))
                except:
                    pass
                # pylinks
                links = []
                for link in self.request.get('links').splitlines():
                    if link[0] == '/':
                        links.append('/api/redir/' + str(s.key().id()) + link)
                    else:
                        links.append(link)
                s.add_links(links)
                s.put()
                s.rm_cache()
                # stats
                st = Stat_cache()
                st.put_page('pylinks', len(links))
                # response
                self.response.headers['Content-Type'] = 'text/plain'
                self.response.out.write( str(s.key()) + "\n" + s.get_link() + "\n" + s.edit_pass + "\n" + self.request.remote_addr)
            except:
                logging.error('Fail to add link to stream -> ' + self.request.get('key'))
                logging.info(self.request.get('links'))
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
                s.rm_cache()
            except:
                logging.error('Fail to close stream -> ' + self.request.get('key'))
                self.error(500)
        else: # lost parameters
            self.error(403)


class Redir_link(webapp.RequestHandler, Basic_tools):
    def get(self, link=None):
        if link:
            aux = link.partition('/')
            try:
                s = Stream.get_by_id( int(aux[0]) )
                if s:
                    url = 'http://' + s.ip + ':' + str(s.port) + '/' + aux[2]
                    if s.ip == self.request.remote_addr:
                        if self.is_ip6(self.request.remote_addr):
                            url = 'http://localhost:' + str(s.port) + '/' + aux[2]
                        elif s.lan_ip:
                            url = 'http://' + s.lan_ip + ':' + str(s.port) + '/' + aux[2]
                    if not s.need_password():
                        self.redirect(url)
                    elif self.user_gives_password(s):
                        self.redirect(url)
                    else:
                        self.redirect('/error/403')
                else:
                    self.redirect('/error/404')
            except:
                logging.warning("Can't redir on: " + link)
                self.redirect('/error/500')
        else:
            self.redirect('/error/403')
    
    def user_gives_password(self, stream):
        if self.request.cookies.get('stream_pass_' + str( stream.key().id() ), '') == stream.access_pass:
            return True
        else:
            return False


class Pylink_exists(webapp.RequestHandler, Basic_tools):
    def get(self):
        self.error(403)
    
    def post(self):
        if self.request.get('version') != PYSTREAM_VERSION: # bad client version
            logging.info('Bad client version! v'+self.request.get('version'))
            self.error(403)
        else:
            pylink = db.GqlQuery("SELECT * FROM Pylink WHERE url = :1", self.request.get('url')).fetch(1)
            if pylink:
                self.response.headers['Content-Type'] = 'text/plain'
                for ori in pylink[0].origin:
                    self.response.out.write(ori + "\n")
            else:
                self.error(403)


class Pylink_check(webapp.RequestHandler, Basic_tools):
    def get(self):
        if self.request.get('version') != PYSTREAM_VERSION: # bad client version
            logging.info('Bad client version! v'+self.request.get('version'))
            self.error(403)
        else:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write( self.get_random_pylink() )
    
    def post(self):
        if self.request.get('version') != PYSTREAM_VERSION: # bad client version
            logging.info('Bad client version! v'+self.request.get('version'))
            self.error(403)
        elif self.request.get('url') and self.request.get('status') and self.request.get('rpkey') == RECAPTCHA_PRIVATE_KEY:
            pylinks = db.GqlQuery("SELECT * FROM Pylink WHERE url = :1", self.request.get('url')).fetch(1)
            if pylinks:
                if self.request.get('filename'):
                    pylinks[0].file_name = self.request.get('filename')
                try:
                    pylinks[0].status = int(self.request.get('status'))
                    pylinks[0].put()
                    pylinks[0].rm_cache()
                    logging.info('Pylink: '+pylinks[0].url+' modified. Filename: '+pylinks[0].file_name+' status: '+str(pylinks[0].status))
                except:
                    logging.warning("Can't modify pylink: " + pylinks[0].url)
        else:
            self.error(403)
    
    def get_random_pylink(self):
        url = ''
        query = db.GqlQuery("SELECT * FROM Pylink WHERE status = :1", 0)
        pylinks = query.fetch(20, random.randint(0, max(0, query.count()-20)))
        if pylinks:
            for pyl in pylinks:
                if pyl.url.find('fileserve.com/list/') == -1 and pyl.url.find('wupload.com/folder/') == -1:
                    url = pyl.url
        else:
            query = db.GqlQuery("SELECT * FROM Pylink WHERE status != :1", 3)
            pylinks = query.fetch(20, random.randint(0, max(0, query.count()-20)))
            if pylinks:
                for pyl in pylinks:
                    if pyl.url.find('fileserve.com/list/') == -1 and pyl.url.find('wupload.com/folder/') == -1:
                        url = pyl.url
        return url


def main():
    application = webapp.WSGIApplication([('/api/hello', Hello),
                                          ('/api/new', New_stream),
                                          ('/api/add_link', Stream_add_link),
                                          ('/api/alive', Stream_alive),
                                          ('/api/close', Close_stream),
                                          (r'/api/redir/(.*)', Redir_link),
                                          ('/api/pylink_exists', Pylink_exists),
                                          ('/api/check', Pylink_check)],
                                         debug=DEBUG_FLAG)
    run_wsgi_app(application)


if __name__ == "__main__":
    main()

