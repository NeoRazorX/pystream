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

class Pyporn:
    PYSTREAM_VERSION = 4
    
    def __init__(self, argv):
        if len(argv) == 1:
            self.PYSTREAM_URL = 'http://www.pystream.com'
        elif len(argv) == 2 and argv[1] == '-l':
            self.PYSTREAM_URL = 'http://localhost:8080'
        elif len(argv) == 3 and argv[1] == '-l':
            self.PYSTREAM_URL = 'http://' + argv[2]
        else:
            self.PYSTREAM_URL = 'http://www.pystream.com'
        self.sitio = ''
        self.videos = []
        self.cargar_feed(0)
        self.procesar_feed()
        self.cargar_feed(2)
        self.procesar_feed()
    
    def cargar_feed(self, eleccion=0):
        if eleccion == 0:
            self.sitio = "xvideos"
            feed_link = "http://www.xvideos.com/rss/rss.xml"
        elif eleccion == 1:
            self.sitio = "redtube"
            feed_link = "http://feeds.feedburner.com/redtube/videos"
        else:
            self.sitio = "youporn"
            feed_link = "http://www.youporn.com/rss"
        print 'Descragando feed de ' + self.sitio
        urllib.urlretrieve(feed_link, '.feed')
        feedfile = open('.feed', 'r')
        readstatus = 0
        self.videos = []
        elemento = {
            'title': '',
            'link': '',
            'image': '',
            'videos': []
        }
        for line in feedfile:
            if self.sitio == 'xvideos':
                if readstatus == 0:
                    if line.find('<item>') != -1:
                        readstatus = 1
                elif readstatus == 1:
                    aux = re.findall(r'<title>(.+?)</title>', line)
                    if aux:
                        elemento['title'] = aux[0]
                        readstatus = 2
                elif readstatus == 2:
                    aux = re.findall(r';http://(.+?).1.jpg', line)
                    if aux:
                        elemento['image'] = 'http://'+aux[0]+'.1.jpg'
                        readstatus = 3
                    aux = re.findall(r'Duration : (.+?)&lt;', line)
                    if aux:
                        elemento['title'] += "\n" + aux[0]
                elif readstatus == 3:
                    aux = re.findall(r'<link>(.+?)</link>', line)
                    if aux:
                        elemento['link'] = aux[0]
                        elemento['videos'] = self.video_links(elemento['link'])
                        self.videos.append(elemento)
                        elemento = {
                            'title': '',
                            'link': '',
                            'image': '',
                            'videos': []
                        }
                        readstatus = 0
            elif self.sitio == 'redtube':
                if readstatus == 0:
                    if line.find('<entry>') != -1:
                        readstatus = 1
                elif readstatus == 1:
                    aux = re.findall(r'<id>(.+?)</id>', line)
                    if aux:
                        elemento['link'] = aux[0]
                        elemento['videos'] = self.video_links(elemento['link'])
                        readstatus = 2
                elif readstatus == 2:
                    aux = re.findall(r'<title>(.+?)</title>', line)
                    if aux:
                        elemento['title'] = aux[0][9:-3]
                        readstatus = 3
                elif readstatus == 3:
                    aux = re.findall(r'Duration: (.+?),', line)
                    if aux:
                        elemento['title'] += "\n" + aux[0]
                        readstatus = 4
                elif readstatus == 4:
                    aux = re.findall(r'<link rel="enclosure" href="(.+?)" type="image/jpeg" length="" />', line)
                    if aux:
                        elemento['image'] = aux[0]
                        self.videos.append(elemento)
                        elemento = {
                            'title': '',
                            'link': '',
                            'image': '',
                            'videos': []
                        }
                        readstatus = 0
            elif self.sitio == 'youporn':
                if readstatus == 0:
                    aux = re.findall(r'<title>(.+?)</title>', line)
                    if aux:
                        elemento['title'] = aux[0][9:-3]
                        readstatus = 1
                elif readstatus == 1:
                    aux = re.findall(r'<link>(.+?)</link>', line)
                    if aux:
                        elemento['link'] = aux[0]
                        elemento['videos'] = self.video_links(elemento['link'])
                        readstatus = 2
                elif readstatus == 2:
                    aux = re.findall(r'Keywords: (.+?)</description>', line)
                    if aux:
                        elemento['title'] += "\n" + aux[0]
                        readstatus = 3
                elif readstatus == 3:
                    aux = re.findall(r'src="(.+?).jpg"', line)
                    if aux:
                        elemento['image'] = aux[0]+'.jpg'
                        self.videos.append(elemento)
                        elemento = {
                            'title': '',
                            'link': '',
                            'image': '',
                            'videos': []
                        }
                        readstatus = 0
            else:
                break
    
    def procesar_feed(self):
        print 'Procesando...'
        for video in self.videos:
            publicar = False
            for v in video['videos']:
                if not self.pylink_exists(v):
                    publicar = True
            if publicar:
                self.publish(video)
    
    def pylink_exists(self, link):
        existe = False
        values = {
            'version': self.PYSTREAM_VERSION,
            'url': link
        }
        print 'Checking if pylink: ' + link + ' exists in pystream'
        try:
            data = urllib.urlencode(values)
            response = urllib2.urlopen(self.PYSTREAM_URL + '/api/pylink_exists', data, timeout=5)
            resp_code = response.getcode()
            if resp_code == 200:
                existe = True
                print 'Exists!'
        except:
            print "No!"
        time.sleep(0.5)
        return existe
    
    def publish(self, video):
        values = {
            'version': self.PYSTREAM_VERSION,
            'machine': platform.uname(),
            'fake': True,
            'public': True,
            'description': video['title']+"\n\n"+self.previews(video['image'])+"\n\n"+video['link'],
            'links': self.list2txt(video['videos'])
        }
        print "Sending new stream..."
        try:
            data = urllib.urlencode(values)
            response = urllib2.urlopen(self.PYSTREAM_URL + '/api/new', data, timeout=20)
            resp_code = response.getcode()
            if resp_code == 200:
                print 'done!'
        except:
            print "Fatal error!"
        time.sleep(0.5)
    
    def previews(self, image):
        previews = image + ' '
        if self.sitio == 'xvideos':
            previews = ''
            aux = image.rsplit(".", 2)
            for num in range(5, 30, 3):
                previews += aux[0] + '.' + str(num) + '.' + aux[2] + ' '
        elif self.sitio == 'redtube':
            previews = ''
            aux = image.rpartition("_")
            for num in range(2, 16):
                if num < 10:
                    previews += aux[0] + '_00' + str(num) + '.jpg '
                else:
                    previews += aux[0] + '_0' + str(num) + '.jpg '
        elif self.sitio == 'youporn':
            aux = re.findall(r'http://(.+?).youporn.com/screenshot/(.+?)/screenshot/(.+?)_extra_large.jpg', image)
            if aux:
                previews = ''
                for num in range(1, 8):
                    previews += 'http://'+aux[0][0]+'.youporn.com/screenshot/'+aux[0][1]+'/screenshot_multiple/'+aux[0][2]+'/'+aux[0][2]+'_multiple_'+str(num)+'_extra_large.jpg '
        return previews
    
    def video_links(self, link):
        url_videos = []
        print 'Checking video link...'
        try:
            response = urllib2.urlopen(link)
            html = response.read()
        except:
            html = ''
        # localizamos la ruta de los archivos mp4
        if self.sitio == 'xvideos':
            aux = re.findall(r'3GP\|\|(.+?)\|\|', html)
            if aux:
                url_videos.append(aux[0])
        elif self.sitio == 'redtube':
            aux = re.findall(r'<source src="(.+?)" type="video/mp4">', html)
            if aux:
                url_videos.append(aux[0])
        elif self.sitio == 'youporn':
            aux = re.findall(r'<a href="http://download.youporn.com/download/(.+?)">', html)
            for a in aux:
                url_videos.append('http://download.youporn.com/download/' + a)
        time.sleep(0.5)
        return url_videos
    
    def list2txt(self, lista):
        text = ''
        for l in lista:
            text += l + "\n"
        return text

if __name__ == "__main__":
    Pyporn(sys.argv)
