#!/usr/bin/env python

import logging, random
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch
from datetime import datetime, timedelta
from base import *


# this class needs to know the local ip to work correctly on local/lan
class Stream_check(webapp.RequestHandler, ip_item):
    def get(self):
        query = db.GqlQuery("SELECT * FROM Stream")
        ss = query.fetch(10, random.randint(0, query.count()-1))
        for s in ss:
            if s.public:
                self.check_public(s)
            else:
                self.check_private(s)
    
    # needed for testing purposes
    def from_local(self, ip):
        if ip == self.request.remote_addr:
            return True
        elif self.request.remote_addr == '127.0.0.1':
            return True
        else:
            return False
    
    def check_online(self, s):
        if self.from_local( self.numToDottedQuad( s.ip ) ):
            result = urlfetch.fetch('http://' + self.numToDottedQuad(s.lan_ip) + ':' + str(s.port))
        else:
            result = urlfetch.fetch('http://' + self.numToDottedQuad(s.ip) + ':' + str(s.port))
        if result.status_code == 200:
            return True
        else:
            return False
    
    # check public avaliability of public streams
    def check_public(self, s):
        try:
            if self.check_online(s):
                s.strikes = 0
                s.online = True
                logging.info('Stream ' + str( s.key().id() ) + ' loaded!')
            else:
                s.strikes += 1
                logging.info('Cant load stream ' + str( s.key().id() ) + '! ' + str(result.status_code) + ' code')
        except:
            s.strikes += 1
            logging.info('Cant load stream ' + str( s.key().id() ) + '!')
        if s.strikes > 5:
            s.rm_comments()
            s.rm_cache()
            s.delete()
            logging.info('Stream ' + str( s.key().id() ) + ' deleted!')
        else:
            s.rm_cache()
            s.put()
    
    # removes private streams after 24 hours
    def check_private(self, s):
        # first and only one online check
        # strikes = -1 -> online, strikes = 1 offline
        # online is only for public streams
        if s.strikes == 0:
            try:
                if self.check_online(s):
                    s.strikes = -1
                else:
                    s.strikes = 1
            except:
                s.strikes = 1
        if s.date < (datetime.today() - timedelta(days=1)):
            s.rm_comments()
            s.rm_cache()
            s.delete()
            logging.info('Stream ' + str( s.key().id() ) + ' deleted!')
        elif s.online: # private streams can't be online
            s.online = False
            s.put()
            s.rm_cache()


def main():
    application = webapp.WSGIApplication([('/cron/stream_check', Stream_check)],
                                            debug=DEBUG_FLAG)
    run_wsgi_app(application)


if __name__ == "__main__":
    main()

