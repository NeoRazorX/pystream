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

DEBUG_FLAG = True
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''
PYSTREAM_VERSION = '2'
RANDOM_CACHE_TIME = 1500

import logging
from google.appengine.ext import db, search
from google.appengine.api import memcache


class Basic_tools:
    def dottedQuadToNum(self, ip):
        try:
            hexn = ''.join(["%02X" % long(i) for i in ip.split('.')])
            return long(hexn, 16)
        except:
            return 0
    
    def numToDottedQuad(self, n):
        d = 256 * 256 * 256
        q = []
        while d > 0:
            m,n = divmod(n,d)
            q.append(str(m))
            d = d/256
        return '.'.join(q)
    
    def get_streams_from_ip(self, ip):
        ss = memcache.get( ip )
        if ss is None:
            ss = db.GqlQuery("SELECT * FROM Stream WHERE ip = :1",
                             self.dottedQuadToNum( ip ) ).fetch(50)
            memcache.add(ip, ss, RANDOM_CACHE_TIME)
            logging.info('memcache add for ip: ' + ip)
        else:
            logging.info('memcache read for ip: ' + ip)
        return ss
    
    def order_streams_date(self, mix):
        finalmix = []
        while len(mix) > 0:
            elem = None
            for m in mix:
                if not elem:
                    elem = m
                elif m.date > elem.date:
                    elem = m
            finalmix.append(elem)
            mix.remove(elem)
        return finalmix
    
    def get_os(self, data):
        os = 'unknown'
        for aux in ['mac', 'iphone', 'ipad', 'ipod', 'windows', 'linux', 'android']:
            if data.lower().find( aux ) != -1:
                os = aux
        return os
    
    def get_lang(self, data):
        if data.lower().find('es') != -1:
            return 'es'
        else:
            return 'en'


class Stream(search.SearchableModel, Basic_tools):
    unsearchable_properties = ['comments', 'date', 'ip', 'lan_ip', 'online',
        'os', 'password', 'port', 'public', 'size', 'strikes']
    comments = db.IntegerProperty(default=0)
    date = db.DateTimeProperty(auto_now_add=True)
    description = db.StringProperty(default='no description')
    ip = db.IntegerProperty(default=0)
    lan_ip = db.IntegerProperty(default=0) # to show on lan
    online = db.BooleanProperty(default=False) # /cron/streams.py will put True if no problem detected
    os = db.StringProperty(default='unknown')
    password = db.StringProperty(default='')
    port = db.IntegerProperty(default=80)
    public = db.BooleanProperty(default=True) # public/private
    size = db.IntegerProperty(default=0)
    strikes = db.IntegerProperty(default=0) # times offline to /cron/streams.py checker
    
    def new_stream(self):
        found = False
        previous = self.get_streams_from_ip( self.full_ip() )
        if previous:
            for p in previous:
                if p.port == self.port:
                    found = True
        if found:
            return False
        else:
            self.put()
            memcache.delete( self.full_ip() )
            return True
    
    def full_ip(self):
        return self.numToDottedQuad( self.ip )
    
    def get_link(self):
        if self.password != '':
            return '/sp/' + str( self.key().id() )
        else:
            return '/s/' + str( self.key().id() )
    
    def get_comments(self):
        comments = memcache.get( str(self.key()) )
        if comments is None:
            query = db.GqlQuery("SELECT * FROM Comment WHERE stream_id = :1 ORDER BY date ASC",
                                self.key().id() )
            numc = query.count()
            comments = query.fetch(numc)
            if self.comments != numc:
                self.comments = numc
                try:
                    self.put()
                except:
                    logging.warning('Cant update the number of comments on stream!')
            if not memcache.add( str(self.key()), comments ):
                logging.warning("Error adding comments to memcache!")
        return comments
    
    def status_text(self):
        status = ''
        if self.public:
            if self.online:
                status = 'public online'
            else:
                status = 'public offline, ' + str(self.strikes) + ' strikes'
        else:
            if self.password != '':
                status = 'password protected, '
            if self.strikes == -1:
                status += 'private online'
            else:
                status += 'private offline'
        return status
    
    def get_results(self):
        return memcache.get('check_results_' + str(self.key().id()))
    
    def rm_comments(self):
        db.delete( Comment.all().filter('stream_id =', self.key().id()) )
    
    def rm_results(self):
        memcache.delete_multi(['cron_stream_checker',
                               'check_results_'+str(self.key().id())])
    
    def rm_cache(self):
        memcache.delete_multi([str(self.key()), 'random_streams', self.full_ip()])
    
    def rm_all(self):
        self.rm_comments()
        self.rm_results()
        self.rm_cache()
        db.delete( self.key() )


class Stream_check_result():
    def __init__(self, ip, sid, res):
        self.ip = int(ip)
        self.stream_id = int(sid)
        self.result = res
    
    def put(self):
        results = memcache.get('check_results_'+str(self.stream_id))
        if results is None:
            results = [self]
            memcache.add('check_results_'+str(self.stream_id), results)
            logging.info('Check results created for stream: '+str(self.stream_id))
        else:
            found = False
            for r in results:
                if r.ip == self.ip and r.stream_id == self.stream_id:
                    found = True
            if not found:
                results.append(self)
                memcache.replace('check_results_'+str(self.stream_id), results)
                logging.info('Check results added for stream: '+str(self.stream_id))
            else:
                logging.info('Check results duplicated for stream: '+str(self.stream_id))


class Machines():
    def __init__(self):
        self.all = memcache.get('all_pystream_machines')
    
    def put(self, machine):
        if machine != '':
            os = 'unknown'
            for aux in ['mac', 'iphone', 'ipad', 'ipod', 'windows', 'linux', 'android']:
                if machine.lower().find( aux ) != -1:
                    os = aux
            if self.all:
                found = False
                for m in self.all:
                    if m[0] == os:
                        m[1] += 1
                        found = True
                if not found:
                    self.all.append([os, 1])
                memcache.replace('all_pystream_machines', self.all)
            else:
                self.all = [[os, 1]]
                memcache.add('all_pystream_machines', self.all)
    
    def get(self):
        return self.all


class Comment(db.Model):
    stream_id = db.IntegerProperty()
    autor = db.StringProperty(default='anonymous')
    text = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    ip = db.IntegerProperty(default=0)
    os = db.StringProperty(default='unknown')
    
    def get_stream(self):
        try:
            s = Stream.get_by_id( self.stream_id )
        except:
            s = None
        return s


class Report(db.Model):
    link = db.LinkProperty()
    text = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    ip = db.IntegerProperty(default=0)
    os = db.StringProperty(default='unknown')
    
    def get_link(self):
        return self.link[23:]


class Stat_item(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    streams = db.IntegerProperty(default=0)
    publics = db.IntegerProperty(default=0)
    online = db.IntegerProperty(default=0)
    sharing = db.IntegerProperty(default=0)
    comments = db.IntegerProperty(default=0)
    reports = db.IntegerProperty(default=0)
    
    def public_relation(self):
        if self.streams > 0 and self.publics > 0:
            return (self.publics*100)/self.streams
        else:
            return 0
    
    def online_relation(self):
        if self.streams > 0 and self.online > 0:
            return (self.online*100)/self.streams
        else:
            return 0
    
    def share_relation(self):
        if self.streams > 0 and self.sharing > 0:
            return self.sharing/self.streams
        else:
            return 0
    
    def comments_relation(self):
        if self.streams > 0 and self.comments > 0:
            return self.comments/self.streams
        else:
            return 0

