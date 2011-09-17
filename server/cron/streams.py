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

class Stream_checker():
    def __init__(self):
        ss = db.GqlQuery("SELECT * FROM Stream WHERE status < :1", 19).fetch(100)
        if ss:
            for s in ss:
                if s.alive < (datetime.datetime.today() - datetime.timedelta(minutes= 30)):
                    s.status = 101
                    try:
                        s.rm_cache()
                        s.put()
                        logging.info("Stream " + s.get_link() + " closed!")
                    except:
                        logging.warning("Can't close stream: " + s.get_link())
        else:
            logging.info('No streams to check :-)')


if __name__ == "__main__":
    sc = Stream_checker()

