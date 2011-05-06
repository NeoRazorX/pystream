#!/usr/bin/env python

DEBUG_FLAG = False
RECAPTCHA_PUBLIC_KEY = '6Ldrqb4SAAAAAOowIidxQ3Hc6igXPdqWKec3dL_H'
RECAPTCHA_PRIVATE_KEY = '6Ldrqb4SAAAAABJ33eyTnkT5t2ll8kKDerqDoNj2'
PYSTREAM_VERSION = '1'
RANDOM_CACHE_TIME = 1200

import logging
from google.appengine.ext import db, search
from google.appengine.api import memcache


class Stream(search.SearchableModel):
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
                logging.error("Error adding comments to memcache!")
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
    
    def rm_comments(self):
        comments = db.GqlQuery("SELECT * FROM Comment WHERE stream_id = :1", self.key().id() )
        db.delete( comments )
    
    def rm_stream_check_result(self):
        rep = db.GqlQuery("SELECT * FROM Stream_check_result WHERE stream_id = :1", self.key().id() )
        db.delete( rep )
    
    def rm_cache(self):
        memcache.delete( str(self.key()) )
        memcache.delete('random_streams')
    
    def rm_all(self):
        self.rm_comments()
        self.rm_stream_check_result()
        self.rm_cache()


class Stream_check_result(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    ip = db.IntegerProperty(default=0)
    stream_id = db.IntegerProperty()
    result = db.StringProperty(default='none')


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


class ip_item:
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

