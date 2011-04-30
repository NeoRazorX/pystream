#!/usr/bin/env python

import logging
from google.appengine.ext import db
from base import *

class Stats():
    def __init__(self):
        si = Stat_item()
        si.streams,si.publics,si.online,si.sharing = self.get_streams()
        si.comments = db.GqlQuery("SELECT * FROM Comment").count()
        si.reports = db.GqlQuery("SELECT * FROM Report").count()
        try:
            si.put()
        except:
            logging.error("Can't save stat item!")
    
    def get_streams(self):
        query = db.GqlQuery("SELECT * FROM Stream")
        ss = 0
        ps = 0
        so = 0
        sh = 0
        for s in query:
            ss += 1
            sh += s.size
            if s.public:
                ps += 1
            if s.online:
                so += 1
        return ss,ps,so,sh
    
if __name__ == "__main__":
    s = Stats()

