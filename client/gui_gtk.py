#!/usr/bin/env python
#
# Author: Carlos Garcia Gomez
# Date: April 11, 2011
# web: http://www.pystream.com

from pystream import *

try:
    import webbrowser
    import pygtk
    pygtk.require('2.0')
    import gtk, gobject
except Exception,e:
	print 'Lost dependency:', e
	sys.exit(1)

gobject.threads_init()


class Pystream_gtk(Mini_gui):
    def __init__(self):
        Mini_gui.__init__(self)
        
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title('pystream')
        self.window.set_icon_from_file('icon.png')
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", gtk.main_quit)
        
        self.vbox = gtk.VBox(homogeneous=False, spacing=10)
        
        self.lb_status = gtk.LinkButton(self.PYSTREAM_URL, label=self.PYSTREAM_URL)
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
        self.cb_upnp = gtk.CheckButton(label='use UPnP')
        self.cb_upnp.set_sensitive(False)
        self.cb_public = gtk.CheckButton(label='public stream')
        self.cb_public.set_active(True)
        self.b_start = gtk.Button(label='Start sharing!')
        self.b_start.connect("clicked", self.start_server, None)
        self.b_start.set_sensitive(False)
        
        self.hbox_top.pack_start(self.label_port, False, False)
        self.hbox_top.pack_start(self.sb_port, False, False)
        self.hbox_top.pack_start(self.cb_upnp, False, False)
        self.hbox_top.pack_start(self.cb_public, True, True)
        self.hbox_top.pack_start(self.b_start, False, False)
        
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll.add(self.text_log)
        
        self.vbox.pack_start(self.lb_status, False, False, 0)
        self.vbox.pack_start(self.scroll, True, True, 0)
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
            self.run_miniserver = False
            try:
                # forces mini server to stop
                response = urllib2.urlopen('http://localhost:' + str( int( self.sb_port.get_value() ) ) )
            except:
                pass
        return False
    
    def start_server(self, widget, data=None):
        self.run_miniserver = True
    
    def write_to_log(self, text):
        buff = self.text_log.get_buffer()
        buff.insert(buff.get_end_iter(), text)
        print text
    
    def set_port(self, port):
        self.sb_port.set_value( port )
    
    def get_port(self):
        return self.sb_port.get_value()
    
    def enable_upnp(self):
        self.cb_upnp.set_sensitive(True)
    
    def set_active_upnp(self, value=False):
        self.cb_upnp.set_active(value)
    
    def is_upnp_avaliable(self):
        return self.cb_upnp.get_active()
    
    def is_public(self):
        return self.cb_public.get_active()
    
    def select_folder(self):
        self.sb_port.set_sensitive(True)
        self.b_start.set_sensitive(True)
        self.scroll.hide()
        self.fc_folder.show()
        self.window.set_title('pystream - select a folder to share')
    
    def get_folder(self):
        return self.fc_folder.get_filename()
    
    def log_mode(self):
        self.fc_folder.hide()
        self.scroll.show()
        self.sb_port.set_sensitive(False)
        self.cb_upnp.set_sensitive(False)
        self.cb_public.set_sensitive(False)
        self.b_start.set_sensitive(False)
    
    def show_link(self, streamid, key):
        webbrowser.open(self.PYSTREAM_URL + '/s/' + streamid + '?key=' + key)
        self.lb_status.set_uri(self.PYSTREAM_URL + '/s/' + streamid)
        self.lb_status.set_label('Show your stream')
        self.lb_status.show()
        self.window.set_title('pystream - sharing')
    
    def retry_share(self):
        self.window.set_title('pystream')
        self.b_start.set_sensitive(True)


if __name__ == "__main__":
    gui = Pystream_gtk()
    server = Mini_server( gui )
    server.start()
    gui.main()

