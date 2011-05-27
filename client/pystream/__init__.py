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

from checker import *
from cloner import *
import os, random, string, platform, re
import SimpleHTTPServer, BaseHTTPServer, SocketServer, socket, cgi
import urllib, urllib2
import thread

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


PYSTREAM_URL = ''
PYSTREAM_VERSION = '2'
PYSTREAM_RUN_WEBSERVER = False
PYSTREAM_LOG = []
PYSTREAM_VIEWS = 0


class Pystream():
    def __init__(self, argv):
        global PYSTREAM_URL
        if len(argv) == 1:
            PYSTREAM_URL = 'http://www.pystream.com'
        elif len(argv) == 2 and argv[1] == '-l':
            PYSTREAM_URL = 'http://localhost:8080'
        elif len(argv) == 3 and argv[1] == '-l':
            PYSTREAM_URL = 'http://' + argv[2]
        else:
            PYSTREAM_URL = 'http://www.pystream.com'
        
        self.quit = False
        self.running_streamchek = False
        self.upnp_up = False
        self.stream_key = self.stream_id = ''
        self.initial_folder = self.target_folder = os.getcwd()
        self.local_ip = self.external_ip = ''
        
        # upnp checking
        self.upnp_loaded = False
        try:
            import miniupnpc
            self.upnp_loaded = True
        except ImportError:
            p_bits, p_os = platform.architecture()
            if p_os == 'ELF':
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
        if self.upnp_loaded:
            self.upnpc = miniupnpc.UPnP()
            self.upnpc.discoverdelay = 200;
    
    def get_pystream_url(self):
        return PYSTREAM_URL
    
    def get_pystream_version(self):
        return PYSTREAM_VERSION
    
    def get_views(self):
        return PYSTREAM_VIEWS
    
    def show_views(self):
        print PYSTREAM_VIEWS
    
    def write_to_log(self, text):
        print text
    
    def check_log(self):
        if PYSTREAM_LOG:
            self.write_to_log( PYSTREAM_LOG.pop() )
        self.show_views()
        return True
    
    def set_port(self, port):
        pass
    
    def get_port(self):
        pass
    
    def enable_upnp(self):
        pass
    
    def set_active_upnp(self, value=False):
        pass
    
    def is_upnp_active(self):
        return False
    
    def is_stream_public(self):
        return False
    
    def is_stream_offline(self):
        return True
    
    def select_folder(self):
        self.write_to_log("Press start button, select a folder and start sharing.")
    
    def get_folder(self):
        return self.target_folder
    
    def log_mode(self):
        pass
    
    def show_link(self, streamid='', key=''):
        pass
    
    def retry_share(self):
        pass
    
    def main(self):
        self.write_to_log("Starting pystream client...")
        self.set_port( random.randint(8081, 60000) )
        upnp_works = False
        # upnp discover
        if self.upnp_loaded:
            self.upnpc.discover()
            try:
                self.upnpc.selectigd()
                self.external_ip = self.upnpc.externalipaddress()
                self.local_ip = self.upnpc.lanaddr
                self.write_to_log("External IP : " + self.external_ip)
                self.write_to_log("Local IP : " + self.local_ip)
                self.enable_upnp()
                upnp_works = True
            except Exception, e:
                print 'Exception :', e
                self.set_active_upnp(False)
                self.write_to_log("Can't use UPnP!")
        else:
            self.set_active_upnp(False)
            self.write_to_log("Can't use UPnP!")
        if not self.upnp_loaded or not upnp_works:
                self.write_to_log("Using alternate mode...")
                self.alternate_get_ip()
                self.write_to_log("Local IP : " + self.local_ip)
        # let user control
        self.select_folder()
    
    def alternate_get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect(("google.com",80))
            self.local_ip = s.getsockname()[0]
            s.close()
        except:
            self.write_to_log("No internet connection!")
    
    def is_port_open(self):
        # need a function to check if external port is open
        return False
        
    def start_webserver(self):
        self.log_mode()
        if self.is_stream_offline():
            # LAN only stream
            thread.start_new_thread(self.run_webserver, ())
            self.show_link()
        else:
            # public/private stream
            if not self.is_port_open():
                if self.is_upnp_active():
                    self.set_upnp()
                elif self.ask_user_upnp():
                    self.set_active_upnp(True)
                    self.set_upnp()
            if self.add_stream():
                self.write_to_log("pystream request done!")
                self.write_to_log("key: " + self.stream_key)
                self.show_link(self.stream_id, self.stream_key)
                thread.start_new_thread(self.run_webserver, ())
            else:
                self.write_to_log("pystream request failed!")
                self.retry_share()
    
    def run_webserver(self):
        global PYSTREAM_RUN_WEBSERVER
        PYSTREAM_RUN_WEBSERVER = True
        os.chdir( self.target_folder )
        port = self.get_port()
        self.write_to_log("Starting web server on http://localhost:" + str(port))
        self.write_to_log("Sharing folder: " + self.target_folder)
        self.write_to_log("\nViews:\n----------------------------------------------------")
        httpd = ThreadedHTTPServer(('', port), MyHandler)
        while PYSTREAM_RUN_WEBSERVER:
            httpd.handle_request()
        print "Web server closed!"
        os.chdir( self.initial_folder )
    
    def stop_webserver(self):
        global PYSTREAM_RUN_WEBSERVER
        PYSTREAM_RUN_WEBSERVER = False
        self.unset_upnp()
    
    def add_stream(self):
        done = False
        values = {
            'version': PYSTREAM_VERSION,
            'port': self.get_port(),
            'lan_ip': self.local_ip,
            'description': self.get_shared_files(),
            'size': self.get_folder_size(),
            'os': platform.uname(),
            'public': self.is_stream_public()
        }
        try:
            self.write_to_log("Sending request...")
            data = urllib.urlencode(values)
            response = urllib2.urlopen( urllib2.Request(PYSTREAM_URL + '/api/new', data), timeout=5)
            resp_code = response.getcode()
            if resp_code == 200:
                resp_text = response.read()
                parts = resp_text.partition(';')
                self.stream_key = parts[0].partition(' ')[2].strip()
                self.stream_id = parts[2].partition(' ')[2].strip()
                if self.stream_key != '' and self.stream_id != '':
                    done = True
                else:
                    self.write_to_log("Error: " + resp_text)
        except urllib2.HTTPError, e:
            self.write_to_log('Response code: ' + str(e.code))
            self.write_to_log("Can't contact to pystream server. Try again later")
        except urllib2.URLError, e:
            self.write_to_log(str(e.args))
            self.write_to_log("Can't contact to pystream server. Try again later")
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
    
    def ask_user_upnp(self):
        return False
    
    def set_upnp(self):
        if not self.upnp_up:
            try:
                self.upnpc.addportmapping(self.get_port(), 'TCP', self.local_ip, self.get_port(), 'pystream', '')
                self.write_to_log("Upnp up!")
                self.upnp_up = True
            except:
                self.set_active_upnp(False)
                self.write_to_log("Can't up Upnp!")
        else:
            self.write_to_log("UPnP already up!")
    
    def unset_upnp(self):
        if self.upnp_up:
            try:
                self.upnpc.deleteportmapping(self.get_port(), 'TCP')
                print "upnp deleted!"
                self.upnp_up = False
            except:
                print "Can't delete upnp!"


class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    def __init__(self, *args):
        BaseHTTPServer.HTTPServer.__init__(self,*args)
    
    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
            self.close_request(request)
        except socket.timeout:
            pass
        except socket.error, e:
            pass
        except:
            self.handle_error(request, client_address)
            self.close_request(request)


class MyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def setup(self):
        self.request.settimeout(2)
        SimpleHTTPServer.SimpleHTTPRequestHandler.setup(self)
    
    def list_directory(self, path):
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))
        f.write("<html>\n<head>\n<title>pystream client</title>\n<link rel='stylesheet' href='" + PYSTREAM_URL + "/css/client.css' type='text/css' />\n</head>\n<body>\n<div class='title'><a href='/'>index</a>%s</div>\n"
                % displaypath)
        f.write('<table>\n<tr>\n<td>\n<ul>\n')
        num = 1
        for name in list:
            if num == 0:
                f.write('</ul>\n</td>\n<td>\n<ul>\n')
                num = 2
            elif num > 15:
                num = 0
            else:
                num += 1
            fullname = os.path.join(path, name)
            linkname = name
            displayname = self.truncate(name, 50)
            filesize = os.path.getsize(fullname)
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname += "/"
                linkname = name + "/"
                f.write('<li><a href="%s" title="%s">%s</a> <span>-</span></li>\n'
                    % (urllib.quote(linkname), linkname, cgi.escape(displayname)))
            elif os.path.islink(fullname):
                pass
            else:
                f.write('<li><a href="%s" title="%s" target="_Blank">%s</a> <span>%s</span></li>\n'
                    % (urllib.quote(linkname), linkname, cgi.escape(displayname), self.show_size(filesize)))
        f.write('</ul>\n</td>\n</tr>\n</table>\n</body>\n</html>\n')
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f
    
    def show_size(self, n):
        if n == '-':
            return n
        elif n < 1024:
            return str(n) + ' bytes'
        elif n < (1000000):
            return str(n/1000) + ' KiB'
        elif n < (1000000000):
            return str(n/1000000) + ' MiB'
        elif n < (1000000000000):
            return str(n/1000000000) + ' GiB'
        else:
            return str(n/1000000000000) + ' TiB'
    
    def log_request(self, code='-', size='-'):
        global PYSTREAM_LOG, PYSTREAM_VIEWS
        PYSTREAM_VIEWS += 1
        PYSTREAM_LOG.append("%s - %s -> %s" % (self.log_date_time_string(), self.address_string(), self.path))
    
    def log_error(self, *args):
        pass
    
    def truncate(self, value, arg):
        try:
            length = int(arg)
        except ValueError: # invalid literal for int()
            return value # Fail silently.
        if not isinstance(value, basestring):
            value = str(value)
        if (len(value) > length):
            return value[:length] + "..."
        else:
            return value
