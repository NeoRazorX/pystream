#!/usr/bin/env python

DEBUG_FLAG = True
RECAPTCHA_PUBLIC_KEY = '6Ldrqb4SAAAAAOowIidxQ3Hc6igXPdqWKec3dL_H'
RECAPTCHA_PRIVATE_KEY = '6Ldrqb4SAAAAABJ33eyTnkT5t2ll8kKDerqDoNj2'

from google.appengine.ext import db
from google.appengine.api import memcache

class Stream(db.Model):
    ip = db.IntegerProperty(default=0)
    port = db.IntegerProperty(default=0)
    date = db.DateTimeProperty(auto_now_add=True)
    
    def get_comments(self, num=100):
        comments = memcache.get( str(self.key()) )
        if comments is None:
            comments = db.GqlQuery("SELECT * FROM Comment WHERE link = :1 ORDER BY date ASC",
                                   'http://www.pystream.com/s/' + str( self.key().id() ) ).fetch( num )
            if not memcache.add( str(self.key()), comments ):
                logging.error("Error adding comments to memcache!")
        return comments
    
    def rm_comments(self):
        comments = db.GqlQuery("SELECT * FROM Comment WHERE link = :1 ORDER BY date ASC",
                               'http://www.pystream.com/s/' + str( self.key().id() ) )
        db.delete( comments )
    
    def rm_cache(self):
        memcache.delete( str(self.key()) )

class Comment(db.Model):
    link = db.LinkProperty()
    autor = db.StringProperty(default='anonymous')
    text = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    ip = db.IntegerProperty(default=0)
