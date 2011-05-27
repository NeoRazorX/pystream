#!/usr/bin/env python
#
# This file is part of Pystream client
# Copyright (c) 2011  Carlos Garcia Gomez ( admin@pystream.com )
#
# Pystream client is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pystream client is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pystream client.  If not, see <http://www.gnu.org/licenses/>.

import re, platform, urllib, urllib2, threading, time

class Stream_checker(threading.Thread):
    def __init__(self, gui):
        threading.Thread.__init__(self)
        self.gui = gui
        self.streams = []
        self.results = {}
    
    def run(self):
        print 'Running stream checker...'
        sleeps = 0
        while not self.gui.quit:
            if sleeps > 0:
                sleeps -= 1
            elif not self.streams and self.results:
                self.send_results()
                sleeps = 300
            elif not self.streams:
                self.request_more_streams()
                if not self.streams:
                    sleeps = 300
            else:
                self.check( self.streams.pop() )
            time.sleep(1)
    
    def request_more_streams(self):
        try:
            print 'Requesting streams to check...'
            response = urllib2.urlopen(self.gui.get_pystream_url() + '/api/check')
            resp_code = response.getcode()
            if resp_code == 200:
                re_stream = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\:\d{1,5}")
                for line in response.readlines():
                    if re_stream.match( line.strip() ):
                        self.streams.append( line.strip() )
        except urllib2.HTTPError, e:
            print 'Response code: ' + str(e.code)
            print "Can't contact to pystream server. Try again later"
        except urllib2.URLError, e:
            print 'Response: ' + str(e.args)
            print "Can't contact to pystream server. Try again later"
            
    
    def check(self, s):
        if len( self.results ) == 0:
            num = '0'
        else:
            num = str( len(self.results)/2 )
        self.results['stream'+num] = s
        try:
            if urllib2.urlopen(url='http://'+s, timeout=2).getcode() == 200:
                self.results['result'+num] = 'online'
        except urllib2.HTTPError, e:
            self.results['result'+num] = 'offline'
        except urllib2.URLError, e:
            self.results['result'+num] = 'offline'
        except:
            self.results['result'+num] = 'error'
        print 'checking stream: ' + self.results['stream'+num] + ' -> ' + self.results['result'+num]
    
    def send_results(self):
        try:
            self.results['version'] = self.gui.get_pystream_version()
            self.results['machine'] = platform.uname()
            data = urllib.urlencode( self.results )
            response = urllib2.urlopen( urllib2.Request(self.gui.get_pystream_url() + '/api/check', data), timeout=5)
            if response.getcode() == 200:
                print 'Results reported'
        except urllib2.HTTPError, e:
            if e.code == 403:
                print "Server said results are bad!"
            else:
                print "Error sending results! " + str(e.code)
        except urllib2.URLError, e:
            print str(e.args)
        except:
            pass
        self.results = {}
