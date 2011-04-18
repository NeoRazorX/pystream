#!/usr/bin/env python

import logging
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch
from datetime import datetime, timedelta
from base import *


# this class needs to know the local ip to work correctly on local/lan
class Stream_check(webapp.RequestHandler, ip_item):
    def get(self):
        ss = db.GqlQuery("SELECT * FROM Stream WHERE date < :1 LIMIT 100",
                         datetime.today() - timedelta(hours= 0))
        for s in ss:
            remove = True
            try:
                if self.from_local( self.numToDottedQuad( s.ip ) ):
                    logging.info('http://' + self.numToDottedQuad(s.lan_ip) + ':' + str(s.port))
                    result = urlfetch.fetch('http://' + self.numToDottedQuad(s.lan_ip) + ':' + str(s.port))
                else:
                    logging.info('http://' + self.numToDottedQuad(s.ip) + ':' + str(s.port))
                    result = urlfetch.fetch('http://' + self.numToDottedQuad(s.ip) + ':' + str(s.port))
                if result.status_code == 200:
                    remove = False
                    logging.info('Stream ' + str( s.key().id() ) + ' loaded!')
                else:
                    logging.info('Cant load stream ' + str( s.key().id() ) + '! ' + str(result.status_code) + ' code')
            except:
                logging.info('Cant load stream ' + str( s.key().id() ) + '!')
            if remove:
                s.rm_comments()
                s.rm_cache()
                s.delete()
                logging.info('Stream ' + str( s.key().id() ) + ' deleted!')
    
    def from_local(self, ip):
        if ip == self.request.remote_addr:
            return True
        elif self.request.remote_addr == '127.0.0.1':
            return True
        else:
            return False


def main():
    application = webapp.WSGIApplication([('/cron/stream_check', Stream_check)],
                                            debug=DEBUG_FLAG)
    run_wsgi_app(application)


if __name__ == "__main__":
    main()

