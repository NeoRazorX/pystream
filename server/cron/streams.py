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

import logging, random, math
from datetime import datetime, timedelta
from base import *

CHECKS_EACH_RUN = 5
CHECKS_BEFORE_REMOVE = 5

class Stream_check(Basic_tools):
    def __init__(self):
        ss = memcache.get('cron_stream_checker')
        if ss is None:
            query = db.GqlQuery("SELECT * FROM Stream")
            ss = query.fetch(100, random.randint(0, max(query.count()-CHECKS_EACH_RUN,0)))
            if ss:
                memcache.add('cron_stream_checker', ss)
                logging.info('memcache add!')
        else:
            logging.info('memcache read!')
        if ss:
            for n in range(CHECKS_EACH_RUN):
                if ss:
                    s = random.choice(ss)
                    try:
                        if s.public:
                            self.check_public( s )
                        else:
                            self.check_private( s )
                    except:
                        logging.error('Error checking stream!')
                    ss.remove( s )
            if ss:
                memcache.replace('cron_stream_checker', ss)
                logging.info(str(len(ss)) + ' streams left!')
            else:
                memcache.delete('cron_stream_checker')
                logging.info('no streams left!')
        else:
            logging.info('no streams!')
    
    # removes public streams after CHECKS_BEFORE_REMOVE strikes
    def check_public(self, s):
        logging.info('checking public stream: ' + s.get_link())
        result = self.process_stream_check_results(s)
        if (s.strikes + result) > CHECKS_BEFORE_REMOVE:
            s.public = False
            s.online = False
            s.strikes = result
            s.put()
            s.rm_cache()
            logging.info('Stream ' + str( s.key().id() ) + ' maded private!')
        elif result >= 0: # offline
            s.strikes += 1
            s.online = False
            s.put()
            s.rm_cache()
            logging.info('Stream ' + str( s.key().id() ) + ' updated!')
        elif result < 0: # online
            if not s.online:
                s.strikes = 0
                s.online = True
                s.put()
                s.rm_cache()
                logging.info('Stream ' + str( s.key().id() ) + ' updated!')
        
    # removes private online streams after 24 hours
    # removes private offline streams after 12 hours
    def check_private(self, s):
        logging.info('checking private stream: ' + s.get_link())
        if s.online: # private streams can't be online
            s.online = False
        result = self.process_stream_check_results(s)
        if result < 0: # online
            if s.date < (datetime.today() - timedelta(hours=24)):
                s.rm_all()
                logging.info('Stream ' + str( s.key().id() ) + ' deleted!')
            elif s.strikes != result:
                s.strikes = result
                s.put()
                s.rm_cache()
                logging.info('Stream ' + str( s.key().id() ) + ' updated!')
        else: # offline
            if s.date < (datetime.today() - timedelta(hours=12)):
                s.rm_all()
                logging.info('Stream ' + str( s.key().id() ) + ' deleted!')
            elif s.strikes != result:
                s.strikes = result
                s.put()
                s.rm_cache()
                logging.info('Stream ' + str( s.key().id() ) + ' updated!')
    
    # read stream check results.
    # -1 = online
    #  0 = unknown
    #  1 = offline
    def process_stream_check_results(self, s):
        logging.info('processing stream: ' + s.get_link())
        strikes = 0
        rr = s.get_results()
        if rr:
            for r in rr:
                if r.result == 'online':
                    strikes -= 1
                elif r.result in ['offline', 'error']:
                    strikes += 1
            logging.info(s.get_link() + ' -> ' + str(len(rr)) + ' check results')
        memcache.delete('check_results_'+str(s.key().id()))
        if strikes > 0:
            return 1
        elif strikes < 0:
            return -1
        else:
            return 0


if __name__ == "__main__":
    Stream_check()

