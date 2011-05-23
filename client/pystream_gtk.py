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

import sys, os, pystream, urllib2

try:
    import webbrowser
    import pygtk
    import gtk, gobject
except Exception,e:
	print 'Lost dependency:', e
	sys.exit(1)

gobject.threads_init()

class Pystream_gtk(pystream.Mini_gui):
    def __init__(self, argv):
        pystream.Mini_gui.__init__(self, argv)
        self.have_indicator = False
        self.have_notify = False
        
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title('pystream')
        self.icon = gtk.gdk.pixbuf_new_from_file('img/icon.png')
        self.window.set_icon_list( self.icon )
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", gtk.main_quit)
        
        menubar = gtk.MenuBar()
        self.filemenu = gtk.Menu()
        mi_client = gtk.MenuItem("Pystream client")
        mi_client.set_sensitive(False)
        self.mi_status = gtk.MenuItem("Status: ready")
        self.mi_status.set_sensitive(False)
        self.mi_clone = gtk.ImageMenuItem('Clone...')
        self.mi_clone.connect("activate", self.clone)
        mi_sep = gtk.SeparatorMenuItem()
        self.mi_show = gtk.CheckMenuItem("Show")
        self.mi_show.set_active(True)
        self.mi_show.connect("activate", self.show_window)
        mi_exit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        mi_exit.connect("activate", self.file_exit)
        self.filemenu.append(mi_client)
        self.filemenu.append(self.mi_status)
        #self.filemenu.append(self.mi_clone)
        self.filemenu.append(mi_sep)
        self.filemenu.append(self.mi_show)
        self.filemenu.append(mi_exit)
        root_menu = gtk.MenuItem("Pystream")
        root_menu.set_submenu(self.filemenu)
        menubar.append(root_menu)
        
        self.lb_status = gtk.LinkButton(self.get_pystream_url(), label=self.get_pystream_url())
        self.label_views = gtk.Label(str(self.get_views()) + ' views ')
        self.text_log = gtk.TextView()
        self.text_log.set_editable(False)
        self.text_log.set_cursor_visible(False)
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll.add(self.text_log)
        
        self.label_port = gtk.Label('Port:')
        self.sb_port = gtk.SpinButton()
        self.sb_port.set_range(1024, 65535)
        self.sb_port.set_increments(1, 50)
        self.sb_port.set_digits(0)
        self.cb_upnp = gtk.CheckButton(label='use UPnP')
        self.cb_upnp.set_sensitive(False)
        self.cb_types = gtk.combo_box_new_text()
        self.cb_types.append_text('public stream')
        self.cb_types.append_text('private stream')
        self.cb_types.append_text('offline stream')
        self.cb_types.set_active(1)
        self.b_start = gtk.Button('start')
        self.b_start.connect("clicked", self.start_server, None)
        
        self.hbox_up = gtk.HBox(homogeneous=False, spacing=5)
        self.hbox_up.pack_start(self.lb_status, True, True)
        self.hbox_up.pack_start(self.label_views, False, False)
        
        self.hbox_down = gtk.HBox(homogeneous=False, spacing=5)
        self.hbox_down.pack_start(self.label_port, False, False)
        self.hbox_down.pack_start(self.sb_port, False, False)
        self.hbox_down.pack_start(self.cb_upnp, False, False)
        self.hbox_down.pack_start(self.cb_types, True, True)
        self.hbox_down.pack_start(self.b_start, False, False)
        
        self.vbox = gtk.VBox(homogeneous=False, spacing=0)
        self.vbox.pack_start(menubar, False, False, 0)
        self.vbox.pack_start(self.hbox_up, False, False, 0)
        self.vbox.pack_start(self.scroll, True, True, 0)
        self.vbox.pack_start(self.hbox_down, False, False, 0)
        
        self.window.add(self.vbox)
        self.window.resize(640, 480)
        self.window.show_all()
        self.hbox_up.hide()
    
    def main(self):
        self.running_gui = True
        gtk.gdk.threads_enter()
        gtk.main()
        gtk.gdk.threads_leave()
        self.running_gui = False
        self.run_miniserver = False
        self.quit = True
    
    def delete_event(self, widget, event, data=None):
        if self.have_indicator:
            self.mi_show.set_active(False)
            self.window.hide()
            if self.have_notify:
                n = pynotify.Notification('pystream-client', message='still running...')
                n.set_icon_from_pixbuf( self.icon )
                n.show()
        else:
            self.mi_status.set_label("Status: closing")
            self.run_miniserver = False
            self.quit = True
            self.close()
        return True
    
    def file_exit(self, widget, data=None):
        self.mi_status.set_label("Status: closing")
        self.run_miniserver = False
        self.quit = True
        self.close()
    
    def close(self):
        self.log_mode()
        if self.running_streamchek:
            self.write_to_log("Stream checker running!\n")
            gobject.timeout_add_seconds(1, self.close)
        elif self.running_miniserver:
            self.write_to_log("Mini-server running!\n")
            try:
                # forces mini server to stop
                response = urllib2.urlopen('http://localhost:' + str(self.get_port()), timeout=1)
            except:
                self.write_to_log("Can't contact mini-server!\n")
            gobject.timeout_add_seconds(1, self.close)
        else:
            gtk.main_quit()
    
    def show_window(self, widget, data=None):
        if widget.active: 
            self.window.show()
        else:
            self.window.hide()
    
    def clone(self, widget, data=None):
        self.write_to_log('clone!')
    
    def start_server(self, widget, data=None):
        fc_folder = gtk.FileChooserDialog('Choose a folder to share',
                                          None,
                                          gtk.FILE_CHOOSER_ACTION_OPEN,
                                          (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                           gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        fc_folder.set_default_response(gtk.RESPONSE_OK)
        fc_folder.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        fc_folder.set_local_only(True)
        if fc_folder.run() == gtk.RESPONSE_OK:
            self.folder = fc_folder.get_filename()
            self.run_miniserver = True
        fc_folder.destroy()
    
    def write_to_log(self, text):
        buff = self.text_log.get_buffer()
        buff.insert(buff.get_end_iter(), text)
        self.text_log.scroll_mark_onscreen( buff.get_insert() )
    
    def set_port(self, port):
        self.sb_port.set_value( port )
    
    def get_port(self):
        return int( self.sb_port.get_value() )
    
    def enable_upnp(self):
        self.cb_upnp.set_sensitive(True)
    
    def set_active_upnp(self, value=False):
        self.cb_upnp.set_active(value)
    
    def is_upnp_active(self):
        return self.cb_upnp.get_active()
    
    def is_public(self):
        return self.cb_types.get_active() == 0
    
    def is_offline(self):
        return self.cb_types.get_active() == 2
    
    def log_mode(self):
        self.hbox_down.hide()
    
    def show_views(self):
        self.label_views.set_label(str(self.get_views()) + ' views ')
    
    def show_link(self, streamid='', key=''):
        if streamid == '' or key == '': #offline
            webbrowser.open('http://localhost:' + str( self.get_port() ))
            self.lb_status.set_uri('http://localhost:' + str( self.get_port() ))
            self.lb_status.set_label('http://localhost:' + str( self.get_port() ))
            self.hbox_up.show()
            self.window.set_title('pystream - sharing: ' + self.get_folder())
            self.mi_status.set_label("Status: sharing offline")
        else:
            webbrowser.open(self.get_pystream_url() + '/s/' + streamid + '?key=' + key)
            self.lb_status.set_uri(self.get_pystream_url() + '/s/' + streamid)
            self.lb_status.set_label(self.get_pystream_url() + '/s/' + streamid)
            self.hbox_up.show()
            self.window.set_title('pystream - sharing: ' + self.get_folder())
            self.mi_status.set_label("Status: sharing")
        if self.have_notify:
            n = pynotify.Notification('pystream-client', message='sharing!')
            n.set_icon_from_pixbuf( self.icon )
            n.show()
    
    def retry_share(self):
        self.window.set_title('pystream')
        self.hbox_down.show()


if __name__ == "__main__":
    gui = Pystream_gtk( sys.argv )
    server = pystream.Mini_server( gui )
    stream_checker = pystream.Stream_checker( gui )
    server.start()
    stream_checker.start()
    
    try:
        import appindicator
        gui.have_indicator = True
    except:
        pass
    
    if gui.have_indicator:
        appind = appindicator.Indicator("pystream-client",
                                        os.getcwd() + "/img/appindicator.png",
                                        appindicator.CATEGORY_APPLICATION_STATUS)
        appind.set_status(appindicator.STATUS_ACTIVE)
        appind.set_attention_icon("nm-adhoc")
        appind.set_menu( gui.filemenu )
    
    try:
        import pynotify
        pynotify.init("pystream-client")
        gui.have_notify = True
    except:
        pass
    
    gui.main()
