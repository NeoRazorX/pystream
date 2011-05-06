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

import os, sys, random, string, platform
import SimpleHTTPServer, BaseHTTPServer, SocketServer, socket, cgi
import urllib, urllib2
import threading, time

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

PYSTREAM_URL = ''
PYSTREAM_VERSION = '1'
MYHANDLER_LOG_LINE = ''
MYHANDLER_VIEWS = 0
MYHANDLER_UPLOADED = 0

class Mini_gui():
    def __init__(self):
        global PYSTREAM_URL
        self.quit = False
        self.run_miniserver = False
        self.running_miniserver = False
        self.running_streamchek = False
        if len(sys.argv) == 1:
            self.PYSTREAM_URL = 'http://www.pystream.com'
        elif len(sys.argv) == 2 and sys.argv[1] == '-l':
            self.PYSTREAM_URL = 'http://localhost:8080'
        elif len(sys.argv) == 3 and sys.argv[1] == '-l':
            self.PYSTREAM_URL = 'http://' + sys.argv[2]
        else:
            self.PYSTREAM_URL = 'http://www.pystream.com'
        PYSTREAM_URL = self.PYSTREAM_URL
    
    def write_to_log(self, text):
        pass
    def set_port(self, port):
        pass
    def get_port(self):
        pass
    def enable_upnp(self):
        pass
    def set_active_upnp(self, value=False):
        pass
    def is_upnp_avaliable(self):
        pass
    def is_public(self):
        pass
    def select_folder(self):
        pass
    def get_folder(self):
        pass
    def log_mode(self):
        pass
    def show_link(self, streamid, key):
        pass
    def retry_share(self):
        pass


class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    def __init__(self, *args):
        BaseHTTPServer.HTTPServer.__init__(self,*args)
    
    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
            self.close_request(request)
        except socket.timeout:
            print 'Timeout during processing of request from',
            print client_address
        except socket.error, e:
            print e, 'during processing of request from',
            print client_address
        except:
            self.handle_error(request, client_address)
            self.close_request(request)


class Mini_server(threading.Thread):
    def __init__(self, gui):
        threading.Thread.__init__(self)
        self.gui = gui
        self.gui.running_miniserver = True
        self.port = random.randint(6000, 9000)
        self.gui.set_port( self.port )
        self.initial_folder = self.target_folder = os.getcwd()
        self.local_ip = self.external_ip = ''
        self.gui.write_to_log("Starting pystream client...\n")
        #
        # upnp checking
        self.upnp_loaded = True
        try:
            import miniupnpc
        except ImportError:
            self.upnp_loaded = False
            p_bits, p_os = platform.architecture()
            if p_bits == '64bit':
                if os.path.exists('miniupnpc_64.so'):
                    os.symlink('miniupnpc_64.so', 'miniupnpc.so')
                    import miniupnpc
                    self.upnp_loaded = True
            else:
                if os.path.exists('miniupnpc_32.so'):
                    os.symlink('miniupnpc_32.so', 'miniupnpc.so')
                    import miniupnpc
                    self.upnp_loaded = True
        except:
            self.upnp_loaded = False
        if self.upnp_loaded:
            self.upnpc = miniupnpc.UPnP()
            self.upnpc.discoverdelay = 200;
    
    def run(self):
        if self.upnp_loaded:
            self.upnpc.discover()
            try:
                self.upnpc.selectigd()
                self.external_ip = self.upnpc.externalipaddress()
                self.local_ip = self.upnpc.lanaddr
                self.gui.write_to_log("External IP : " + self.external_ip + "\n")
                self.gui.write_to_log("Local IP : " + self.local_ip + "\n")
                self.gui.enable_upnp()
                self.gui.set_active_upnp(True)
            except Exception, e:
                print 'Exception :', e
                self.gui.set_active_upnp(False)
                self.gui.write_to_log("Can't use UPnP!\n")
        else:
            self.gui.set_active_upnp(False)
            self.gui.write_to_log("Can't use UPnP!\n")
        if not self.upnp_loaded or not self.gui.is_upnp_avaliable():
                self.gui.write_to_log("Using alternate mode...\n")
                self.alternate_get_ip()
                self.gui.write_to_log("Local IP : " + self.local_ip + "\n")
        
        # let user control
        self.gui.select_folder()
        
        while not self.gui.quit:
            if self.gui.run_miniserver:
                # updating data
                self.port = self.gui.get_port()
                self.target_folder = self.gui.get_folder()
                # disabling user control
                self.gui.log_mode()
                
                if self.gui.is_upnp_avaliable():
                    self.set_upnp()
                os.chdir( self.target_folder )
                
                if self.add_stream():
                    self.gui.write_to_log("pystream request done!\n")
                    self.gui.show_link(self.stream_id, self.stream_key)
                    self.run_webserver()
                else:
                    self.gui.run_miniserver = False
                    self.gui.write_to_log("pystream request failed!\n")
                    self.gui.retry_share()
                
                os.chdir( self.initial_folder )
                if self.gui.is_upnp_avaliable():
                    self.unset_upnp()
            else:
                time.sleep(0.2)
        self.gui.running_miniserver = False
    
    def alternate_get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect(("google.com",80))
            self.local_ip = s.getsockname()[0]
            s.close()
        except:
            self.gui.write_to_log("Fatal error: no internet connection\n")
    
    def run_webserver(self):
        global MYHANDLER_LOG_LINE
        self.gui.write_to_log("Starting web server on http://localhost:" + str(self.port) + "\n")
        self.gui.write_to_log("Sharing folder: " + self.target_folder + "\n")
        self.gui.write_to_log("\nViews:\n----------------------------------------------------\n")
        httpd = ThreadedHTTPServer(('', self.port), MyHandler)
        while self.gui.run_miniserver:
            httpd.handle_request()
            self.gui.write_to_log( MYHANDLER_LOG_LINE )
        self.gui.write_to_log("Web server closed!\n")
    
    def add_stream(self):
        done = False
        values = {
            'version': PYSTREAM_VERSION,
            'port': self.port,
            'lan_ip': self.local_ip,
            'description': self.get_shared_files(),
            'size': self.get_folder_size(),
            'os': platform.uname(),
            'public': self.gui.is_public()
        }
        try:
            self.gui.write_to_log("Sending request...\n")
            data = urllib.urlencode(values)
            response = urllib2.urlopen( urllib2.Request(self.gui.PYSTREAM_URL + '/new', data), timeout=2)
            resp_code = response.getcode()
            if resp_code == 200:
                resp_text = response.read()
                parts = resp_text.partition(';')
                self.stream_key = parts[0].partition(' ')[2].strip()
                self.stream_id = parts[2].partition(' ')[2].strip()
                if self.stream_key != '' and self.stream_id != '':
                    done = True
                else:
                    self.gui.write_to_log("Error:\n" + resp_text + "\n")
            else:
                self.gui.write_to_log('Response code: ' + resp_code + "\n")
        except:
            self.gui.write_to_log("Can't contact to pystream server. Try again later\n")
        return done
    
    def get_shared_files(self):
        files = os.listdir( self.target_folder )
        text = ''
        i = False
        for filename in files:
            if filename[0] != '.':
                if i:
                    text += ', '
                else:
                    i = True
                text += filename
        return text
    
    def get_folder_size(self):
        folder_size = 0
        for (path, dirs, files) in os.walk( self.target_folder ):
            for file in files:
                filename = os.path.join(path, file)
                folder_size += os.path.getsize(filename)
        return folder_size
    
    def set_upnp(self):
        try:
            self.upnpc.addportmapping(self.port, 'TCP', self.local_ip, self.port, 'pystream', '')
            self.gui.write_to_log("Upnp up!\n")
        except:
            self.gui.write_to_log("Can't up Upnp!\n")
    
    def unset_upnp(self):
        try:
            self.upnpc.deleteportmapping(self.port, 'TCP')
            self.gui.write_to_log("upnp deleted!\n")
        except:
            self.gui.write_to_log("Can't delete upnp!\n")


class MyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def setup(self):
        self.request.settimeout(60)
        SimpleHTTPServer.SimpleHTTPRequestHandler.setup(self)
    
    def list_directory(self, path):
        global MYHANDLER_VIEWS
        global MYHANDLER_UPLOADED
        global PYSTREAM_URL
        MYHANDLER_VIEWS += 1
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))
        f.write("<html>\n<head>\n<title>pystream client</title>\n<link rel='stylesheet' href='" + PYSTREAM_URL + "/css/client.css' type='text/css' />\n</head>\n<body>\n<div class='title'>Folder: %s</div>\n"
                % displaypath)
        f.write('<table>\n')
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.write('<tr><td class="file"><a href="%s">%s</a></td></tr>\n'
                    % (urllib.quote(linkname), cgi.escape(displayname)))
        f.write('</table>\n<br/><br/>\n<div class="title">Stats:</div>Views: %d, Uploaded: %s, Thread: %s\n</body>\n</html>\n'
                % (MYHANDLER_VIEWS, self.show_size(MYHANDLER_UPLOADED), threading.currentThread().getName()))
        length = f.tell()
        MYHANDLER_UPLOADED += length
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f
    
    def show_size(self, n):
        if n < 1024:
            return str(n) + ' bytes'
        elif n < (1000000):
            return str(n/1000) + ' KiB'
        elif n < (1000000000):
            return str(n/1000000) + ' MiB'
        elif n < (1000000000000):
            return str(n/1000000000) + ' GiB'
        else:
            return str(n/1000000000000) + ' TiB'
    
    def log_request(self, code=200, size=0):
        global MYHANDLER_LOG_LINE
        MYHANDLER_LOG_LINE = self.log_date_time_string() + ', ' + self.address_string() + ' looking for ' + self.path + ' - ' + str(code) + "\n"
    
    def LogErr(self, s):
        pass


class Stream_checker(threading.Thread):
    def __init__(self, gui):
        threading.Thread.__init__(self)
        self.gui = gui
        self.gui.running_streamchek = True
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
                sleeps = 1200
            elif not self.streams:
                self.request_more_streams()
            else:
                self.check( self.streams.pop() )
            time.sleep(1)
        self.gui.running_streamchek = False
    
    def request_more_streams(self):
        try:
            print "Requesting streams to check..."
            response = urllib2.urlopen(self.gui.PYSTREAM_URL + '/stream_check')
            resp_code = response.getcode()
            if resp_code == 200:
                for line in response.readlines():
                    self.streams.append( line.strip() )
            else:
                print 'Response code: ' + resp_code
        except:
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
            else:
                self.results['result'+num] = 'offline'
        except:
            self.results['result'+num] = 'error'
        print 'checking stream: ' + self.results['stream'+num] + ' -> ' + self.results['result'+num]
    
    def send_results(self):
        try:
            data = urllib.urlencode( self.results )
            response = urllib2.urlopen( urllib2.Request(self.gui.PYSTREAM_URL + '/stream_check', data), timeout=5)
            if response.getcode() == 200:
                print "Results reported"
            else:
                print "Server said results are bad!"
        except:
            print "Error sending results!"
        self.results = {}
