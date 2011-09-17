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

import logging, random, re
from google.appengine.ext import db
from google.appengine.api import urlfetch
from base import *

class Pylink_checker(Basic_tools):
    def __init__(self):
        if random.randint(0, 3) < 3:
            query = db.GqlQuery("SELECT * FROM Pylink WHERE status = :1", 0)
            pylinks = query.fetch(5, random.randint(0, max(0, query.count()-1)))
            if pylinks:
                logging.info('Cheking unknown pylinks...')
            else:
                logging.info('No pylinks to check!')
        else:
            query = db.GqlQuery("SELECT * FROM Pylink WHERE status != :1", 3)
            pylinks = query.fetch(5, random.randint(0, max(0, query.count()-1)))
            logging.info('Cheking random pylinks...')
        for pyl in pylinks:
            if pyl.url[:11] == '/api/redir/': # from pystream sharing tool
                self.pst_link(pyl)
            elif pyl.url[:7] == 'http://':
                status_code = 0
                content = ''
                try:
                    result = urlfetch.fetch( pyl.url )
                    status_code = result.status_code
                    content = result.content
                except:
                    logging.warning("Can't check pylink: " + pyl.url)
                if status_code == 200:
                    if pyl.url.find('megaupload.com') != -1:
                        self.megaupload(pyl, content)
                    elif pyl.url.find('fileserve.com/file/') != -1:
                        self.fileserve_file(pyl, content)
                    elif pyl.url.find('fileserve.com/list/') != -1:
                        self.fileserve_list(pyl, content)
                    elif pyl.url.find('mediafire.com/?') != -1:
                        self.mediafire(pyl, content)
                    elif pyl.url.find('wupload.com/file/') != -1:
                        self.wupload_file(pyl, content)
                    elif pyl.url.find('wupload.com/folder/') != -1:
                        self.wupload_list(pyl, content)
                    else:
                        pyl.status = 3
                        try:
                            pyl.put()
                            pyl.rm_cache()
                            logging.info('Pylink ' + pyl.url + ' online!')
                        except:
                            logging.warning("Can't modify pylink:" + pyl.url)
                else:
                    pyl.status = 3
                    try:
                        pyl.put()
                        pyl.rm_cache()
                        logging.info('Pylink ' + pyl.url + ' offline!')
                    except:
                        logging.warning("Can't modify pylink:" + pyl.url)
            else: # no http link
                self.no_http_link(pyl)
    
    def pst_link(self, pyl):
        try:
            pyl.status = 3
            pyl.file_name = pyl.url.rpartition('/')[2]
            pyl.put()
            pyl.rm_cache()
        except:
            logging.warning("(pst) Can't modify pylink:" + pyl.url)
    
    def no_http_link(self, pyl):
        if pyl.url[:13] == 'ed2k://|file|':
            pyl.status = 3
            file_name = re.findall('ed2k://|file|(.+?)|', pyl.url)
            if file_name:
                pyl.filename = file_name[0]
            try:
                pyl.put()
                pyl.rm_cache()
            except:
                logging.warning("(ed2k) Can't modify pylink:" + pyl.url)
        else:
            logging.warning("Unknown link type:" + pyl.url)
    
    def megaupload(self, pyl, html):
        if html.find('down_butt_pad1') != -1:
            found = re.findall('<span class="down_txt2">(.+?)</span>', html)
            if found:
                pyl.file_name = found[0]
            pyl.status = 1
            logging.info('(megaupload) Pylink ' + pyl.url + ' online!')
        else:
            pyl.status = 2
            logging.info('(megaupload) Pylink ' + pyl.url + ' offline!')
        try:
            pyl.put()
            pyl.rm_cache()
        except:
            logging.warning("(megaupload) Can't modify pylink:" + pyl.url)
    
    def fileserve_file(self, pyl, html):
        if html.find('downloadBox1') != -1:
            found = re.findall('<h1>(.+?)<br/></h1>', html)
            if found:
                pyl.file_name = found[0]
            pyl.status = 1
            logging.info('(fileserve) Pylink ' + pyl.url + ' online!')
        else:
            pyl.status = 2
            logging.info('(fileserve) Pylink ' + pyl.url + ' offline!')
        try:
            pyl.put()
            pyl.rm_cache()
        except:
            logging.warning("(fileserve) Can't modify pylink:" + pyl.url)
    
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
    
    def mediafire(self, pyl, html):
        if html.find('download_file_title') != -1:
            found = re.findall('<div class="download_file_title" style="margin:20px 0; word-break:break-word;"> (.+?) <div', html)
            if found:
                pyl.file_name = found[0]
            pyl.status = 1
            logging.info('(mediafire) Pylink ' + pyl.url + ' online!')
        else:
            pyl.status = 2
            logging.info('(mediafire) Pylink ' + pyl.url + ' offline!')
        try:
            pyl.put()
            pyl.rm_cache()
        except:
            logging.warning("(mediafire) Can't modify pylink:" + pyl.url)
    
    def wupload_file(self, pyl, html):
        if html.find('fileInfo filename') != -1:
            found = re.findall('<span>Filename: </span> <strong>(.+?)</strong>', html)
            if found:
                pyl.file_name = found[0]
            pyl.status = 1
            logging.info('(wupload) Pylink ' + pyl.url + ' online!')
        else:
            pyl.status = 2
            logging.info('(wupload) Pylink ' + pyl.url + ' offline!')
        try:
            pyl.put()
            pyl.rm_cache()
        except:
            logging.warning("(wupload) Can't modify pylink:" + pyl.url)
    
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
    pylc = Pylink_checker()

