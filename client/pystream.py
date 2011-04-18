#!/usr/bin/env python
#
# Author: Carlos Garcia Gomez
# Date: April 11, 2011
# web: http://www.pystream.com

import os, sys, random, string

try:
    import SimpleHTTPServer, SocketServer
    import urllib, urllib2, webbrowser
    import pygtk
    pygtk.require('2.0')
    import gtk, threading, time, gobject
except Exception,e:
	print 'Lost dependency:', e
	sys.exit(1)

gobject.threads_init()

if len(sys.argv) == 1:
    PYSTREAM_URL = 'http://www.pystream.com'
elif sys.argv[1] == '-l':
    PYSTREAM_URL = 'http://localhost:8080'
else:
    PYSTREAM_URL = 'http://www.pystream.com'

PYSTREAM_VERSION = '1'

class Pystream_gui():
    def __init__(self):
        self.quit = False
        self.run_miniserver = False
        
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title('pystream')
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", gtk.main_quit)
        
        self.vbox = gtk.VBox(homogeneous=False, spacing=10)
        
        self.lb_status = gtk.LinkButton(PYSTREAM_URL, label=PYSTREAM_URL)
        self.text_log = gtk.TextView()
        self.text_log.set_editable(False)
        self.text_log.set_cursor_visible(False)
        self.fc_folder = gtk.FileChooserWidget(action=gtk.FILE_CHOOSER_ACTION_OPEN, backend=None)
        self.fc_folder.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        self.fc_folder.set_local_only(True)
        
        self.hbox_top = gtk.HBox(homogeneous=False, spacing=5)
        
        self.label_port = gtk.Label('Port:')
        self.sb_port = gtk.SpinButton()
        self.sb_port.set_range(1024, 65535)
        self.sb_port.set_increments(1, 50)
        self.sb_port.set_digits(0)
        self.sb_port.set_sensitive(False)
        self.b_start = gtk.Button(label='Start sharing!')
        self.b_start.connect("clicked", self.start_server, None)
        self.b_start.set_sensitive(False)
        
        self.hbox_top.pack_start(self.label_port, False, False)
        self.hbox_top.pack_start(self.sb_port, False, False)
        self.hbox_top.pack_start(self.b_start, True, True)
        
        self.vbox.pack_start(self.lb_status, False, False, 0)
        self.vbox.pack_start(self.text_log, True, True, 0)
        self.vbox.pack_start(self.fc_folder, True, True, 0)
        self.vbox.pack_start(self.hbox_top, False, False, 0)
        
        self.window.add(self.vbox)
        self.window.resize(640, 480)
        self.window.show_all()
        self.fc_folder.hide()
        self.lb_status.hide()
    
    def main(self):
        gtk.gdk.threads_enter()
        gtk.main()
        gtk.gdk.threads_leave()
    
    def delete_event(self, widget, event, data=None):
        self.quit = True
        if self.run_miniserver:
            print('Closing mini server...')
            self.run_miniserver = False
            try:
                # forces mini server to stop
                response = urllib2.urlopen('http://localhost:' + str( int( self.sb_port.get_value() ) ) )
            except:
                print('Conection refused!')
        return False
    
    def start_server(self, widget, data=None):
        self.run_miniserver = True


class Mini_server(threading.Thread):
    def __init__(self, gui):
        threading.Thread.__init__(self)
        self.gui = gui
        self.gui.quit = False
        self.gui.run_miniserver = False
        self.port = random.randint(6000, 9000)
        self.gui.sb_port.set_value( self.port )
        self.initial_folder = self.current_folder = os.getcwd()
        self.local_ip = self.external_ip = ''
        self.text_buffer = self.gui.text_log.get_buffer()
        self.write_to_log("Starting pystream client...\n")
    
    def run(self):
        output = os.popen('./upnpc-static -s')
        for line in output.readlines():
            if line.find('Local LAN ip address : ') > -1:
                aux = line.rpartition(' ')
                self.local_ip = aux[2].strip()
            elif line.find('ExternalIPAddress = ') > -1:
                aux = line.rpartition(' ')
                self.external_ip = aux[2].strip()
        if output.close() == None:
            self.write_to_log("External IP : " + self.external_ip + "\n")
            self.write_to_log("Local IP : " + self.local_ip + "\n")
        else:
            self.write_to_log(output + "\n")
        
        # let user control
        self.gui.sb_port.set_sensitive(True)
        self.gui.b_start.set_sensitive(True)
        self.gui.text_log.hide()
        self.gui.fc_folder.show()
        
        while not self.gui.quit:
            if self.gui.run_miniserver:
                # updating data
                self.port = int( self.gui.sb_port.get_value() )
                self.current_folder = self.gui.fc_folder.get_filename()
                # disbling user control
                self.gui.fc_folder.hide()
                self.gui.text_log.show()
                self.gui.sb_port.set_sensitive(False)
                self.gui.b_start.set_sensitive(False)
                
                self.set_upnp()
                os.chdir( self.current_folder )
                
                if self.add_stream():
                    self.gui.lb_status.set_uri(PYSTREAM_URL + '/s/' + self.stream_id)
                    self.gui.lb_status.show()
                    self.write_to_log("pystream request done!\n")
                    self.run_webserver()
                else:
                    self.write_to_log("pystream request failed!\n")
                
                os.chdir( self.initial_folder )
                self.unset_upnp()
            else:
                time.sleep(0.2)
        
        # closing
        print self.text_buffer.get_text(self.text_buffer.get_start_iter(), self.text_buffer.get_end_iter())
    
    def run_webserver(self):
        self.write_to_log("Starting web server on " + self.current_folder + " ...\n")
        httpd = SocketServer.TCPServer(('', self.port), SimpleHTTPServer.SimpleHTTPRequestHandler)
        while self.gui.run_miniserver:
            httpd.handle_request()
        httpd.server_close()
        self.write_to_log("Web server closed!\n")
    
    def write_to_log(self, text):
        self.text_buffer.insert(self.text_buffer.get_end_iter(), text)
    
    def add_stream(self):
        done = False
        values = {
            'version': PYSTREAM_VERSION,
            'ip': self.external_ip,
            'port': self.port,
            'lan_ip': self.local_ip
        }
        try:
            data = urllib.urlencode(values)
            response = urllib2.urlopen( urllib2.Request(PYSTREAM_URL + '/new', data) )
            resp_code = response.getcode()
            resp_text = response.read()
            if resp_code == 200:
                parts = resp_text.partition(';')
                self.stream_key = parts[0].partition(' ')[2].strip()
                self.stream_id = parts[2].partition(' ')[2].strip()
                if self.stream_key != '' and self.stream_id != '':
                    done = True
                    webbrowser.open(PYSTREAM_URL + '/s/' + self.stream_id + '?key=' + self.stream_key)
                else:
                    self.write_to_log("Error!\n" + resp_text + "\n")
            else:
                self.write_to_log('Response code: ' + resp_code + "\n")
        except Exception, detail:
            self.write_to_log("Err " + detail + "\n")
        return done
    
    def set_upnp(self):
        output = os.popen('./upnpc-static -a ' + self.local_ip + ' ' + str(self.port) + ' ' + str(self.port) + ' TCP')
        if output.close() == None:
            self.write_to_log("Upnp up!\n")
        else:
            self.write_to_log("Can't up Upnp!\n")
    
    def unset_upnp(self):
        output = os.popen('./upnpc-static -d ' + str(self.port) + ' TCP')
        if output.close() == None:
            self.write_to_log("upnp deleted!\n")
        else:
            self.write_to_log("Can't delete upnp!\n")


if __name__ == "__main__":
    gui = Pystream_gui()
    server = Mini_server( gui )
    server.start()
    gui.main()

