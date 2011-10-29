#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
        # closing bad streams
        bads = db.GqlQuery("SELECT * FROM Stream WHERE status < :1", 19).fetch(100)
        if bads:
            for s in bads:
                if s.alive < (datetime.datetime.today() - datetime.timedelta(minutes= 30)):
                    s.status = 101
                    try:
                        s.rm_cache()
                        s.put()
                        logging.info("Stream " + s.get_link() + " closed!")
                    except:
                        logging.warning("Can't close bad stream: " + s.get_link())
        else:
            logging.info('No bad streams to check :-)')
        # removing old streams
        olds = db.GqlQuery("SELECT * FROM Stream WHERE date < :1", datetime.datetime.today() - datetime.timedelta(days= 30)).fetch(10)
        if olds:
            logging.info(str(len(olds)) + ' old streams to check :-)')
            for s in olds:
                if s.is_closed():
                    try:
                        s.rm_all()
                        logging.info("Stream " + s.get_link() + " removed!")
                    except:
                        logging.warning("Can't remove stream: " + s.get_link())
        else:
            logging.info('No old streams to check :-)')


if __name__ == "__main__":
    Stream_checker()
