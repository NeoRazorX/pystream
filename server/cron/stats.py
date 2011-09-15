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

import logging, datetime
from google.appengine.ext import db
from base import *

class Stats():
    def __init__(self):
        aux = db.GqlQuery("SELECT * FROM Stat_item WHERE date >= :1", datetime.date.today()).fetch(1)
        if aux is None:
            si = Stat_item()
        elif len(aux) == 1:
            si = aux[0]
        else:
            si = Stat_item()
        st = Stat_cache()
        summary = st.get_summary()
        today = datetime.date.today()
        si.comments = max(si.comments, db.GqlQuery("SELECT * FROM Comment WHERE date >= :1", today).count(), summary['comments'])
        si.downloads = max(si.downloads, summary['downloads'])
        si.ip6 = max(si.ip6, summary['ip6'])
        si.upnp = max(si.upnp, summary['upnp'])
        si.machines = max(si.machines, summary['machines'])
        si.pylinks = max(si.pylinks, db.GqlQuery("SELECT * FROM Pylink WHERE date >= :1", today).count(), summary['pylinks'])
        si.reports = max(si.reports, db.GqlQuery("SELECT * FROM Report").count())
        si.requests = max(si.requests, db.GqlQuery("SELECT * FROM Request WHERE date >= :1", today).count(), summary['requests'])
        si.searches = max(si.searches, summary['searches'])
        si.streams = max(si.streams, db.GqlQuery("SELECT * FROM Stream WHERE date >= :1", today).count(), summary['streams'])
        try:
            si.put()
        except:
            logging.error("Can't save stat item!")
    
if __name__ == "__main__":
    s = Stats()

