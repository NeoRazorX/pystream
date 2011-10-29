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

import sys, platform, urllib, urllib2, re, time

class Pylink_checker():
    PYSTREAM_VERSION = 4
    RECAPTCHA_PRIVATE_KEY = ''
    
    def __init__(self, argv):
        if len(argv) == 1:
            self.PYSTREAM_URL = 'http://www.pystream.com'
        elif len(argv) == 2 and argv[1] == '-l':
            self.PYSTREAM_URL = 'http://localhost:8080'
        elif len(argv) == 3 and argv[1] == '-l':
            self.PYSTREAM_URL = 'http://' + argv[2]
        else:
            self.PYSTREAM_URL = 'http://www.pystream.com'
        for i in range(100):
            url = self.get_pylink()
            if url != '':
                self.check_pylink(url)
            else:
                break
    
    def get_pylink(self):
        url = ''
        print 'Get pylink to check...'
        try:
            response = urllib2.urlopen(self.PYSTREAM_URL + '/api/check?version='+str(self.PYSTREAM_VERSION), timeout=5)
            resp_code = response.getcode()
            if resp_code == 200:
                url = response.read()
                print url
        except:
            print "Fail!"
        time.sleep(0.5)
        return url
    
    def check_pylink(self, url):
        if url[:7] == 'http://':
            status_code = 0
            content = ''
            try:
                response = urllib2.urlopen(url, timeout=5)
                status_code = response.getcode()
            except:
                print "Can't check url: " + url
            if status_code == 200:
                if url.find('megaupload.com') != -1:
                    self.megaupload(url, response)
                elif url.find('fileserve.com/file/') != -1:
                    self.fileserve_file(url, response)
                elif url.find('mediafire.com/?') != -1:
                    self.mediafire(url, response)
                elif url.find('wupload.com/file/') != -1:
                    self.wupload_file(url, response)
                else:
                    if url.find('?') != -1:
                        filename = url.rpartition('/')[2].rpartition('?')[0]
                    else:
                        filename = url.rpartition('/')[2]
                    print 'online!'
                    self.send_results(url, filename, 1)
            else:
                if url.find('?') != -1:
                    filename = url.rpartition('/')[2].rpartition('?')[0]
                else:
                    filename = url.rpartition('/')[2]
                print 'offline!'
                self.send_results(url, filename, 2)
        elif url != '': # no http link
            self.no_http_link(url)
        else:
            print 'No url to check!'
    
    def send_results(self, url, filename, status):
        values = {
            'version': self.PYSTREAM_VERSION,
            'rpkey': self.RECAPTCHA_PRIVATE_KEY,
            'url': url,
            'filename': filename,
            'status': status
        }
        print "Sending results..."
        try:
            data = urllib.urlencode(values)
            response = urllib2.urlopen(self.PYSTREAM_URL + '/api/check', data, timeout=20)
            resp_code = response.getcode()
            if resp_code == 200:
                print 'done!'
        except:
            print "Fatal error!"
        time.sleep(0.5)
    
    def no_http_link(self, url):
        if url[:13] == 'ed2k://|file|':
            aux = re.findall('ed2k://|file|(.+?)|', url)
            if aux:
                filename = aux[0]
            else:
                filename = ''
            self.send_results(url, filename, 3)
        else:
            print "Unknown link type:" + url
    
    def megaupload(self, url, response):
        html = response.read()
        filename = ''
        status = 2
        if html.find('down_butt_pad1') != -1:
            found = re.findall('<span class="down_txt2">(.+?)</span>', html)
            if found:
                filename = found[0]
            status = 1
            print '(megaupload) Pylink ' + url + ' online!'
        else:
            print '(megaupload) Pylink ' + url + ' offline!'
        self.send_results(url, filename, status)
    
    def fileserve_file(self, url, response):
        html = response.read()
        filename = ''
        status = 2
        if html.find('downloadBox1') != -1:
            found = re.findall('<h1>(.+?)<br/></h1>', html)
            if found:
                filename = found[0]
            status = 1
            print '(fileserve) Pylink ' + url + ' online!'
        else:
            print '(fileserve) Pylink ' + url + ' offline!'
        self.send_results(url, filename, status)
    
    def mediafire(self, url, response):
        html = response.read()
        filename = ''
        status = 2
        if html.find('download_file_title') != -1:
            found = re.findall('<div class="download_file_title" style="margin:20px 0; word-break:break-word;"> (.+?) <div', html)
            if found:
                filename = found[0]
            status = 1
            print '(mediafire) Pylink ' + url + ' online!'
        else:
            print '(mediafire) Pylink ' + url + ' offline!'
        self.send_results(url, filename, status)
    
    def wupload_file(self, url, response):
        html = response.read()
        filename = ''
        status = 2
        if html.find('fileInfo filename') != -1:
            found = re.findall('<span>Filename: </span> <strong>(.+?)</strong>', html)
            if found:
                filename = found[0]
            status = 1
            print '(wupload) Pylink ' + url + ' online!'
        else:
            print '(wupload) Pylink ' + url + ' offline!'
        self.send_results(url, filename, status)


if __name__ == "__main__":
    Pylink_checker(sys.argv)
