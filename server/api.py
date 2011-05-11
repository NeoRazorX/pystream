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

import cgi, os, random, math
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from base import *


class New_stream(webapp.RequestHandler, ip_item):
    def get(self):
        self.error(403)
    
    def post(self):
        if self.request.get('version') != PYSTREAM_VERSION: # bad client version
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write('Bad version! You need to download a new client -> http://www.pystream.com/new')
            logging.warning('Bad client version!')
        elif self.request.get('port') and (self.request.get('ip') or self.request.get('lan_ip')): # client request
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
                if s.new_stream():
                    self.response.headers['Content-Type'] = 'text/plain'
                    self.response.out.write('key: ' + str( s.key() ) + ';id: ' + str( s.key().id() ) )
                else:
                    self.error(403)
            except:
                logging.error('Fail to store stream -> ' + self.request.get('ip') + ':' + self.request.get('port'))
                self.error(500)
        else: # lost parameters
            self.error(403)


class Stream_checking(webapp.RequestHandler, ip_item):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        ss = self.get_streams()
        for s in ss:
            self.response.out.write(s + "\n")
    
    def get_streams(self):
        mix = []
        finalmix = []
        # append near streams
        ss = self.get_streams_from_ip( self.request.remote_addr )
        if ss:
            for s in ss:
                mix.append(self.numToDottedQuad(s.lan_ip) + ':' + str(s.port))
        # append public streams
        if len(mix) < 20:
            query = db.GqlQuery("SELECT * FROM Stream WHERE public = :1", True)
            ss = query.fetch(10, random.randint(0, max(query.count()-10, 0)))
            if ss:
                for s in ss:
                    # filter near streams
                    if self.numToDottedQuad(s.ip) != self.request.remote_addr:
                        mix.append(self.numToDottedQuad(s.ip) + ':' + str(s.port))
        logging.info(str(len(mix)) + ' streams found!')
        # random order
        if mix:
            for n in range(20):
                if mix:
                    elem = random.choice(mix)
                    finalmix.append(elem)
                    mix.remove(elem)
        return finalmix
    
    def post(self):
        if self.request.get('version') != PYSTREAM_VERSION: # bad client version
            self.error(403)
        else:
            try:
                self.load_streams_for_results()
                for n in range(20):
                    if self.request.get('stream'+str(n)) != '':
                        self.read_result(self.request.get('stream'+str(n)),
                                         self.request.get('result'+str(n)))
            except:
                self.error(500)
    
    def load_streams_for_results(self):
        self.allss = self.get_streams_from_ip( self.request.remote_addr )
        ips = []
        if self.allss:
            for n in range(20):
                if self.request.get('stream'+str(n)) != '':
                    ip = self.dottedQuadToNum( self.request.get('stream'+str(n)).partition(':')[0] )
                    port = int( self.request.get('stream'+str(n)).partition(':')[2] )
                    found = False
                    for s in self.allss:
                        if s.ip == self.dottedQuadToNum(self.request.remote_addr) and s.lan_ip == ip and s.port == port:
                            found = True
                    if not found and ip not in ips:
                        ips.append(ip)
                        logging.info('Need to read for ip: ' + self.request.get('stream'+str(n)).partition(':')[0])
        else:
            logging.info('No near streams found in memcache!')
            for n in range(20):
                if self.request.get('stream'+str(n)) != '':
                    ip = self.dottedQuadToNum( self.request.get('stream'+str(n)).partition(':')[0] )
                    if ip not in ips:
                        ips.append(ip)
                        logging.info('Need to read for ip: ' + self.request.get('stream'+str(n)).partition(':')[0])
        if ips:
            logging.info('GQL read needed!')
            aux = db.GqlQuery("SELECT * FROM Stream WHERE ip IN :1", ips).fetch(20)
            for a in aux:
                self.allss.append( a )
        else:
            logging.info('No need to GQL read!')
    
    def read_result(self, stream, result):
        try:
            ip = self.dottedQuadToNum( stream.partition(':')[0] )
            port = int( stream.partition(':')[2] )
            remote_ip = self.dottedQuadToNum( self.request.remote_addr )
            
            if self.allss:
                for s in self.allss:
                    if s.ip == remote_ip and s.lan_ip == ip and s.port == port: # near stream
                        Stream_check_result(remote_ip, s.key().id(), result).put()
                    elif s.ip == ip and s.port == port:
                        Stream_check_result(remote_ip, s.key().id(), result).put()
            else:
                logging.info('Fake stream: ' + stream)
        except:
            logging.warning("Error processing result: " + stream + ' -> ' + result)


def main():
    application = webapp.WSGIApplication([('/api/new', New_stream),
                                          ('/api/check', Stream_checking)],
                                         debug=DEBUG_FLAG)
    run_wsgi_app(application)


if __name__ == "__main__":
    main()

