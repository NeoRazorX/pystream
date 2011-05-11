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

