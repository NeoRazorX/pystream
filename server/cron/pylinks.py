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

import logging, random, re
from google.appengine.ext import db
from google.appengine.api import urlfetch
from base import *

class Pylink_checker(Basic_tools):
    def __init__(self):
        query = db.GqlQuery("SELECT * FROM Pylink WHERE status = :1", 0)
        pylinks = query.fetch(5, random.randint(0, max(0, query.count()-5)))
        if pylinks:
            logging.info('Cheking unknown pylinks...')
            for pyl in pylinks:
                if pyl.url.find('fileserve.com/list/') != -1 or pyl.url.find('wupload.com/folder/') != -1:
                    status_code = 0
                    content = ''
                    try:
                        result = urlfetch.fetch( pyl.url )
                        status_code = result.status_code
                        content = result.content
                    except:
                        logging.warning("Can't check pylink: " + pyl.url)
                    if status_code == 200:
                        if pyl.url.find('fileserve.com/list/') != -1:
                            self.fileserve_list(pyl, content)
                        elif pyl.url.find('wupload.com/folder/') != -1:
                            self.wupload_list(pyl, content)
                    else:
                        pyl.status = 2
                        try:
                            pyl.put()
                            pyl.rm_cache()
                            logging.info('Pylink ' + pyl.url + ' offline!')
                        except:
                            logging.warning("Can't modify pylink:" + pyl.url)
        else:
            logging.info('No pylinks to check!')
    
    def fileserve_list(self, pyl, html):
        links = []
        files = re.findall('href="/file/(.+?)"', html)
        for f in files:
            links.append('http://www.fileserve.com/file/' + f)
        pylinks = self.new_pylinks(links, pyl.origin[0])
        if pylinks:
            logging.info('(fileserve_list) ' + len(pylinks + ' pylinks created!'))
            try:
                pyl.rm_cache()
                db.delete( pyl.key() )
                logging.info('(fileserve_list) Pylink ' + pyl.url + ' removed succesfull!')
            except:
                logging.warning("(fileserve_list) Can't remove pylink:" + pyl.url)
        else:
            try:
                pyl.status = 2
                pyl.put()
                pyl.rm_cache()
                logging.info('(fileserve_list) Pylink ' + pyl.url + ' offline!')
            except:
                logging.warning("(fileserve_list) Can't modify pylink:" + pyl.url)
    
    def wupload_list(self, pyl, html):
        links = []
        files = re.findall('/file/(.+?)"', html)
        for f in files:
            links.append('http://www.wupload.com/file/' + f)
        pylinks = self.new_pylinks(links, pyl.origin[0])
        if pylinks:
            logging.info('(wupload_list) ' + len(pylinks + ' pylinks created!'))
            try:
                pyl.rm_cache()
                db.delete( pyl.key() )
                logging.info('(wupload_list) Pylink ' + pyl.url + ' removed succesfull!')
            except:
                logging.warning("(wupload_list) Can't remove pylink:" + pyl.url)
        else:
            try:
                pyl.status = 2
                pyl.put()
                pyl.rm_cache()
                logging.info('(wupload_list) Pylink ' + pyl.url + ' offline!')
            except:
                logging.warning("(wupload_list) Can't modify pylink:" + pyl.url)


if __name__ == "__main__":
    Pylink_checker()
