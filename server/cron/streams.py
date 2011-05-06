#!/usr/bin/env python

import logging, random, math
from datetime import datetime, timedelta
from base import *

CHECKS_EACH_RUN = 10
CHECKS_BEFORE_REMOVE = 3

class Stream_check(ip_item):
    def __init__(self):
        query = db.GqlQuery("SELECT * FROM Stream ORDER BY date DESC")
        ss = query.fetch(CHECKS_EACH_RUN,
                         random.randint(0, max(query.count()-CHECKS_EACH_RUN+1,0)))
        for s in ss:
            if s.public:
                self.check_public(s)
            else:
                self.check_private(s)
    
    # removes public streams after CHECKS_BEFORE_REMOVE strikes
    def check_public(self, s):
        result = self.process_stream_check_results(s)
        if s.strikes > CHECKS_BEFORE_REMOVE:
            s.rm_all()
            s.delete()
            logging.info('Stream ' + str( s.key().id() ) + ' deleted!')
        elif result >= 0: # offline
            s.strikes += 1
            s.online = False
            s.rm_cache()
            s.put()
        elif result < 0: # online
            s.strikes = 0
            s.online = True
            s.rm_cache()
            s.put()
    
    # removes private online streams after 24 hours
    # removes private offline streams after 12 hours
    def check_private(self, s):
        if s.online: # private streams can't be online
            s.online = False
        s.strikes = self.process_stream_check_results(s)
        if s.strikes <= 0: # online or unknown
            if s.date < (datetime.today() - timedelta(hours=24)):
                s.rm_all()
                s.delete()
                logging.info('Stream ' + str( s.key().id() ) + ' deleted!')
            else:
                s.put()
        else: # offline
            if s.date < (datetime.today() - timedelta(hours=12)):
                s.rm_all()
                s.delete()
                logging.info('Stream ' + str( s.key().id() ) + ' deleted!')
            else:
                s.put()
    
    # read stream check results.
    # -1 = online
    #  0 = unknown
    #  1 = offline
    def process_stream_check_results(self, s):
        strikes = 0
        ips = []
        rr = db.GqlQuery("SELECT * FROM Stream_check_result WHERE stream_id = :1 ORDER BY stream_id ASC", s.key().id())
        for r in rr:
            if r.ip not in ips:
                if r.result == 'online':
                    strikes -= 1
                elif r.result == 'offline':
                    strikes += 1
                elif r.result == 'error':
                    strikes += 1
                ips.append(r.ip)
        db.delete(rr)
        if strikes > 0:
            return 1
        elif strikes < 0:
            return -1
        else:
            return 0


if __name__ == "__main__":
    Stream_check()

