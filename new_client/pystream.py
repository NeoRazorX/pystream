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


try:
    import sys, os, platform, socket, urllib, urllib2, re
    import thread, SimpleHTTPServer, BaseHTTPServer, SocketServer
    import pygtk, gtk, gobject
except Exception,e:
    print 'Lost dependency:', e
    sys.exit(1)


class New_client:
    PYSTREAM_VERSION = 3
    port = 8081
    
    def __init__(self, argv):
        if len(argv) == 1:
            self.PYSTREAM_URL = 'http://www.pystream.com'
        elif len(argv) == 2 and argv[1] == '-l':
            self.PYSTREAM_URL = 'http://localhost:8080'
        elif len(argv) == 3 and argv[1] == '-l':
            self.PYSTREAM_URL = 'http://' + argv[2]
        else:
            self.PYSTREAM_URL = 'http://www.pystream.com'
        self.stream_key = ''
        self.stream_link = ''
        self.gui()
    
    def gui(self):
        self.gtkb = gtk.Builder()
        self.gtkb.add_from_file('gui.glade')
        self.window = self.gtkb.get_object('mainwindow')
        self.window.set_title('Pystream ' + str(self.PYSTREAM_VERSION))
        self.window.set_icon_from_file('icon.png')
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", gtk.main_quit)
        self.lb_online = self.gtkb.get_object('lb_online')
        self.lb_lan = self.gtkb.get_object('lb_lan')
        self.fcb_folder = self.gtkb.get_object('fcb_folder')
        self.fcb_folder.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        self.sb_port = self.gtkb.get_object('sb_port')
        self.sb_port.set_range(1024, 65535)
        self.sb_port.set_increments(1, 50)
        self.sb_port.set_digits(0)
        self.sb_port.set_value(self.port)
        self.cb_visibility = self.gtkb.get_object('cb_visibility')
        liststore = gtk.ListStore(str)
        self.cb_visibility.set_model( liststore )
        cell = gtk.CellRendererText()
        self.cb_visibility.pack_start(cell, True)
        self.cb_visibility.add_attribute(cell, 'text', 0)  
        self.cb_visibility.append_text('Public')
        self.cb_visibility.append_text('Private')
        self.cb_visibility.append_text('LAN only')
        self.cb_visibility.set_active(0)
        self.b_start = self.gtkb.get_object('b_start')
        self.b_start.connect("clicked", self.gui_start_button, False)
        self.tv_log = self.gtkb.get_object('tv_log')
        self.window.show()
        self.initialize_network()
        gtk.gdk.threads_enter()
        gtk.main()
        gtk.gdk.threads_leave()
    
    def initialize_network(self):
        self.upnpc = Upnp_client()
        if self.upnpc.is_ip6():
            self.write2log('IPv6 detected!')
            self.write2log('IP: ' + self.upnpc.local_ip)
        else:
            self.write2log('Local IP: ' + self.upnpc.local_ip)
            self.write2log('External IP: ' + self.upnpc.external_ip)
            if self.upnpc.is_working():
                self.write2log('UPnP support working!')
            else:
                self.write2log('UPnP support not working!')
        values = {
            'version': self.PYSTREAM_VERSION,
            'machine': platform.uname(),
            'upnp': self.upnpc.is_working()
        }
        try:
            self.write2log("Sending hello request...")
            data = urllib.urlencode(values)
            response = urllib2.urlopen(self.PYSTREAM_URL + '/api/hello', data, timeout=2)
            resp_code = response.getcode()
            if resp_code == 200:
                self.write2log("Pystream server said: Hello!")
            else:
                self.write2log("Error: " + str(resp_code))
        except urllib2.HTTPError, e:
            self.write2log('Response code: ' + str(e.code))
        except urllib2.URLError, e:
            self.write2log( str(e.args) )
        except:
            self.write2log("Fatal error!")
    
    def delete_event(self, widget, event, data=None):
        self.upnpc.delete_port_mapping( int(self.sb_port.get_value()) )
        self.send_close()
    
    def write2log(self, text):
        try:
            buff = self.tv_log.get_buffer()
            buff.insert(buff.get_end_iter(), text+"\n")
            self.tv_log.scroll_mark_onscreen( buff.get_insert() )
        except:
            print text
    
    def gui_start_button(self, widget, data=False):
        self.b_start.set_sensitive(False)
        self.fcb_folder.set_sensitive(False)
        self.sb_port.set_sensitive(False)
        self.cb_visibility.set_sensitive(False)
        if self.is_stream_offline():
            self.lb_lan.set_uri('http://' + self.upnpc.local_ip + ':' + str(int(self.sb_port.get_value())))
            self.lb_lan.set_label('http://' + self.upnpc.local_ip + ':' + str(int(self.sb_port.get_value())))
            self.lb_lan.set_sensitive(True)
            thread.start_new_thread(self.run_webserver, ())
            self.write2log('Serving...')
        else:
            self.new_stream( self.fcb_folder.get_filename() )
            if self.stream_key != '' and self.stream_link != '':
                self.lb_online.set_uri(self.PYSTREAM_URL + self.stream_link)
                self.lb_online.set_label(self.PYSTREAM_URL + self.stream_link)
                self.lb_online.set_sensitive(True)
                self.lb_lan.set_uri('http://' + self.upnpc.local_ip + ':' + str(int(self.sb_port.get_value())))
                self.lb_lan.set_label('http://' + self.upnpc.local_ip + ':' + str(int(self.sb_port.get_value())))
                self.lb_lan.set_sensitive(True)
                thread.start_new_thread(self.run_webserver, ())
                self.upnpc.add_port_mapping( int(self.sb_port.get_value()) )
                self.write2log('Serving...')
                gobject.timeout_add_seconds(3, self.send_alive)
    
    def is_stream_public(self):
        return self.cb_visibility.get_active() == 0
    
    def is_stream_offline(self):
        return self.cb_visibility.get_active() == 2
    
    def run_webserver(self):
        global PYSTREAM_RUN_WEBSERVER
        PYSTREAM_RUN_WEBSERVER = True
        os.chdir( self.fcb_folder.get_filename() )
        port = int(self.sb_port.get_value())
        httpd = ThreadedHTTPServer(('', port), SimpleHTTPServer.SimpleHTTPRequestHandler)
        while PYSTREAM_RUN_WEBSERVER:
            httpd.handle_request()
        os.chdir( self.initial_folder )
        self.upnpc.add_port_mapping(port)
    
    def new_stream(self, folder):
        result = False
        if folder:
            if os.path.exists(folder):
                values = {
                    'version': self.PYSTREAM_VERSION,
                    'machine': platform.uname(),
                    'port': self.port,
                    'links': self.get_shared_files(folder),
                    'public': self.is_stream_public()
                }
                try:
                    self.write2log("Sending new stream request...")
                    data = urllib.urlencode(values)
                    response = urllib2.urlopen(self.PYSTREAM_URL + '/api/new', data, timeout=5)
                    resp_code = response.getcode()
                    if resp_code == 200:
                        lines = response.read().splitlines()
                        self.stream_key = lines[0]
                        self.stream_link = lines[1]
                        self.write2log('New stream ready!')
                    else:
                        self.write2log("Error: " + str(resp_code))
                except urllib2.HTTPError, e:
                    self.write2log('Response code: ' + str(e.code))
                except urllib2.URLError, e:
                    self.write2log( str(e.args) )
                except:
                    self.write2log("Fatal error!")
        return result
    
    def get_shared_files(self, folder):
        text = ''
        for filename in os.listdir(folder):
            text += '/' + filename + "\n"
        return text
    
    def send_alive(self):
        if self.stream_key:
            values = {
                'version': self.PYSTREAM_VERSION,
                'machine': platform.uname(),
                'key': self.stream_key
            }
            try:
                self.write2log("Sending alive message...")
                data = urllib.urlencode(values)
                response = urllib2.urlopen(self.PYSTREAM_URL + '/api/alive', data, timeout=5)
                resp_code = response.getcode()
                if resp_code == 200:
                    self.write2log('Alive!')
                else:
                    self.write2log("Error: " + str(resp_code))
            except urllib2.HTTPError, e:
                self.write2log('Response code: ' + str(e.code))
            except urllib2.URLError, e:
                self.write2log( str(e.args) )
            except:
                self.write2log("Fatal error!")
        return True
    
    def send_close(self):
        if self.stream_key:
            values = {
                'version': self.PYSTREAM_VERSION,
                'machine': platform.uname(),
                'key': self.stream_key
            }
            try:
                self.write2log("Sending close message...")
                data = urllib.urlencode(values)
                response = urllib2.urlopen(self.PYSTREAM_URL + '/api/close', data, timeout=5)
                resp_code = response.getcode()
                if resp_code == 200:
                    self.write2log('Close!')
                else:
                    self.write2log("Error: " + str(resp_code))
            except urllib2.HTTPError, e:
                self.write2log('Response code: ' + str(e.code))
            except urllib2.URLError, e:
                self.write2log( str(e.args) )
            except:
                self.write2log("Fatal error!")


class Upnp_client:
    loaded = False
    works = False
    mapped = False
    external_ip = ''
    local_ip = ''
    
    def __init__(self):
        try:
            import miniupnpc
            self.loaded = True
        except ImportError:
            p_bits, p_os = platform.architecture()
            if p_os == 'ELF':
                if p_bits == '64bit':
                    if os.path.exists('miniupnpc_64.so'):
                        os.symlink('miniupnpc_64.so', 'miniupnpc.so')
                        import miniupnpc
                        self.loaded = True
                else:
                    if os.path.exists('miniupnpc_32.so'):
                        os.symlink('miniupnpc_32.so', 'miniupnpc.so')
                        import miniupnpc
                        self.loaded = True
        if self.loaded:
            self.upnpc = miniupnpc.UPnP()
            self.upnpc.discoverdelay = 200;
            self.upnpc.discover()
            try:
                self.upnpc.selectigd()
                self.external_ip = self.upnpc.externalipaddress()
                self.local_ip = self.upnpc.lanaddr
                self.works = True
            except:
                pass
        if not self.loaded or not self.works:
            self.alternate_get_ip()
    
    def alternate_get_ip(self):
        if self.local_ip == '':
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(1)
                s.connect(("www.pystream.com",80))
                self.local_ip = s.getsockname()[0]
                s.close()
            except:
                self.write2log("No internet connection!")
    
    def is_working(self):
        if self.loaded and self.works:
            return True
        else:
            return False
    
    def is_ip6(self):
        pattern = re.compile(r'(?:(?<=::)|(?<!::):)', re.VERBOSE | re.IGNORECASE | re.DOTALL)
        if self.local_ip != '':
            return pattern.match( self.local_ip ) is not None
        elif self.external_ip != '':
            return pattern.match( self.external_ip ) is not None
        else:
            return False
    
    def add_port_mapping(self, port):
        if self.loaded and self.works:
            if self.upnpc.addportmapping(port, 'TCP', self.local_ip, port, 'pystream', ''):
                self.mapped = True
    
    def delete_port_mapping(self, port):
        if self.mapped:
            if self.upnpc.deleteportmapping(port, 'TCP'):
                self.mapped = False


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


if __name__ == "__main__":
    
    gobject.threads_init()
    ncli = New_client( sys.argv )
