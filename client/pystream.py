#!/usr/bin/env python
#
# Author: Carlos Garcia Gomez
# Date: April 11, 2011
# web: http://www.pystream.com

import os, sys

try:
    import random, string, signal, SimpleHTTPServer, SocketServer, urllib, urllib2, webbrowser
except Exception,e:
	print 'Lost dependency:', e
	sys.exit(1)

class Pystream():
    PYSTREAM_URL = 'http://localhost:8080'
    
    def __init__(self):
        # get current folder
        self.CURRENT_FOLDER = os.getcwd()
        
        # select random port
        self.PORT = random.randint(6000, 9000)
        print "Selected port: " + str(self.PORT)
        
        if len( sys.argv ) > 1:
            # setup upnp
            self.set_upnp()
            
            # setup signal handler
            signal.signal(signal.SIGINT, self.signal_handler)
            
            # send request to pystream.com
            if self.add_stream():
                print "pystream request done!"
                
                # move to selected folder
                os.chdir( sys.argv[1] )
                
                # start http server
                print "Starting web server..."
                httpd = SocketServer.TCPServer(("", self.PORT), SimpleHTTPServer.SimpleHTTPRequestHandler)
                httpd.serve_forever()
            else:
                print "pystream request failed!"
            self.unset_upnp()
    
    def set_upnp(self):
        output = os.popen('./upnpc-static -s')
        for line in output.readlines():
            if line.find('Local LAN ip address : ') > -1:
                aux = line.rpartition(' ')
                self.LOCAL_IP = aux[2].strip()
            elif line.find('ExternalIPAddress = ') > -1:
                aux = line.rpartition(' ')
                self.EXTERNAL_IP = aux[2].strip()
        print "Local IP : " + self.LOCAL_IP
        print "External IP : " + self.EXTERNAL_IP
        os.popen('./upnpc-static -a ' + self.LOCAL_IP + ' ' + str(self.PORT) + ' ' + str(self.PORT) + ' TCP')
        print "Upnp up!"
    
    def add_stream(self):
        done = False
        values = {
            'ip': self.EXTERNAL_IP,
            'port': self.PORT
        }
        try:
            data = urllib.urlencode(values)
            req = urllib2.Request(self.PYSTREAM_URL + '/new', data)
            response = urllib2.urlopen(req)
            if response.getcode() == 200:
                parts = response.read().partition(';')
                self.STREAM_KEY = parts[0].partition(' ')[2].strip()
                self.STREAM_ID = parts[2].partition(' ')[2].strip()
                webbrowser.open(self.PYSTREAM_URL + '/s/' + self.STREAM_ID + '?key=' + self.STREAM_KEY)
                done = True
        except Exception, detail:
            print "Err ", detail
        return done
    
    def unset_upnp(self):
        # move to original folder
        os.chdir( self.CURRENT_FOLDER )
        # unsetup upnp
        os.popen('./upnpc-static -d ' + str(self.PORT) + ' TCP')
        print "upnp deleted"
    
    def signal_handler(self, signal, frame):
        self.unset_upnp()
        print "Closing..."
        sys.exit(0)

if __name__ == "__main__":
    Pystream()

