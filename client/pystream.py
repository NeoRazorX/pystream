#!/usr/bin/env python
#
# Author: Carlos Garcia Gomez
# Date: April 11, 2011
# web: http://www.pystream.com

import os, sys

try:
    import random, string, signal, SimpleHTTPServer, SocketServer
except Exception,e:
	print 'Lost dependency:', e
	sys.exit(1)

class Pystream():
    def __init__(self):
        # get current folder
        self.CURRENT_FOLDER = os.getcwd()
        
        # select random port
        self.PORT = random.randint(6000, 9000)
        print "Selected port: " + str(self.PORT)
        
        if len( sys.argv ) > 1:
            # setup upnp
            output = os.popen('./upnpc-static -s')
            for line in output.readlines():
                if line.find('Local LAN ip address : ') > -1:
                    aux = line.rpartition(' ')
                    self.LOCAL_IP = aux[2].strip()
            print "Local IP : " + self.LOCAL_IP
            os.popen('./upnpc-static -a ' + self.LOCAL_IP + ' ' + str(self.PORT) + ' ' + str(self.PORT) + ' TCP')
            
            # setup signal handler
            signal.signal(signal.SIGINT, self.signal_handler)
            
            # move to selected folder
            os.chdir( sys.argv[1] )
            
            # start http server
            print "Starting web server..."
            httpd = SocketServer.TCPServer(("", self.PORT), SimpleHTTPServer.SimpleHTTPRequestHandler)
            httpd.serve_forever()
    
    def signal_handler(self, signal, frame):
        # move to original folder
        os.chdir( self.CURRENT_FOLDER )
        
        # unsetup upnp
        os.popen('./upnpc-static -d ' + str(self.PORT) + ' TCP')
        print "Closing..."
        sys.exit(0)

if __name__ == "__main__":
    Pystream()

