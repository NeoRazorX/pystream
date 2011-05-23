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

import os, re, urllib, urllib2, threading, time, random

class Stream_cloner(threading.Thread):
    def __init__(self, gui):
        threading.Thread.__init__(self)
        self.gui = gui
        self.clone_started = False
        self.file_list = []
        self.black_list = []
    
    def run(self):
        self.gui.running_streamcloner = True
        print 'Running stream cloner...'
        while not self.gui.quit:
            if self.gui.start_clone and self.gui.url_to_clone != '':
                if not self.clone_started:
                    self.starting_clone()
                else:
                    self.cloning()
            time.sleep(1)
        self.gui.running_streamcloner = False
    
    def starting_clone(self):
        self.gui.write_to_log("Initializing clone...\n")
        baseurl = self.gui.get_pystream_url()
        if baseurl+'/s/' in self.gui.url_to_clone:
            try:
                streamid = self.gui.url_to_clone[len(baseurl)+4:]
                request = urllib2.urlopen(url=baseurl+'/api/redir/'+streamid, timeout=2)
                if request.getcode() == 200:
                    self.gui.url_to_clone = baseurl+'/api/redir/'+streamid
                    self.get_links( request.read() )
                    self.gui.write_to_log("Clone process ready, press the start button!\n")
                    self.clone_started = True
                else:
                    self.gui.start_clone = False
            except:
                self.gui.write_to_log("Can't read stream! Try again later...\n")
                self.gui.start_clone = False
        elif 'http://boards.4chan.org/' in self.gui.url_to_clone:
            try:
                request = urllib2.urlopen(url=self.gui.url_to_clone, timeout=2)
                if request.getcode() == 200:
                    self.get_links( request.read() )
                    self.gui.write_to_log("Clone process ready, press the start button!\n")
                    self.clone_started = True
                else:
                    self.gui.start_clone = False
            except:
                self.gui.write_to_log("Can't read stream! Try again later...\n")
                self.gui.start_clone = False
        else:
            self.gui.write_to_log("Bad URL!\n")
            self.gui.start_clone = False
    
    def cloning(self):
        if self.file_list and self.gui.run_miniserver:
            elem = random.choice( self.file_list )
            aux = elem.rpartition('/')
            filename = aux[ len( aux ) -1 ]
            if os.path.exists( filename ):
                self.gui.write_to_log('File ' + filename + " already downloaded!\n")
            elif filename != '':
                self.gui.write_to_log('Downloading: ' + filename + "\n")
                #urllib.urlretrieve(elem, filename)
            else:
                self.gui.write_to_log("Can't download: " + elem + "\n")
            self.file_list.remove(elem)
    
    def get_links(self, html, num=0):
        aux = re.findall(r'href=[\'"]?([^\'" >]+)', html)
        if aux:
            for a in aux:
                if a[:7] != 'http://':
                    a = self.gui.url_to_clone + a
                if a[-1:] == '/' and num < 1 and self.gui.url_to_clone in a and a not in self.black_list:
                    print 'Searching on: ' + a
                    self.black_list.append(a)
                    self.get_links(urllib2.urlopen(url=a, timeout=5).read(), num+1)
                elif a not in self.file_list and a[-1:] != '/':
                    self.file_list.append(a)
                    print 'Add: ' + a
                else:
                    self.black_list.append(a)
        else:
            self.gui.write_to_log("No links found!\n")

