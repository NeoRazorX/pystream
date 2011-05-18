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

from pystream_core import *

try:
    import webbrowser
    from Tkinter import *
    import tkFileDialog
except Exception,e:
	print 'Lost dependency:', e
	sys.exit(1)


class Pystream_tk(Mini_gui):
    def __init__(self):
        Mini_gui.__init__(self)
        self.streamid = ''
        self.key = ''
        
        self.window = Tk()
        p_bits, p_os = platform.architecture()
        if p_os == 'WindowsPE':
            self.window.iconbitmap('img/icon.ico')
        elif p_os == 'ELF':
            self.window.iconbitmap('@img/icon.xbm')
        self.window.protocol("WM_DELETE_WINDOW", self.close_event)
        self.window.title('Pystream client')
        self.window.minsize(500,400)
        
        self.frame_up = Frame(self.window)
        self.frame_up.pack(fill=BOTH)
        self.b_link = Button(self.frame_up, text=self.get_pystream_url(), command=self.open_link)
        #self.b_link.pack(side=LEFT, expand=True, fill=BOTH)
        self.b_link['state'] = 'disabled'
        self.label_views = Label(self.frame_up, text=str(self.get_views())+' views ')
        #self.label_views.pack(side=RIGHT)
        self.textlog = Text()
        self.textlog.pack(expand=True, fill=BOTH)
        self.textlog['state'] = 'disabled'
        labelport = Label(text='Port:')
        labelport.pack(side=LEFT)
        self.port_var = StringVar()
        self.port = Spinbox(width=5, from_=1024, to=65535, textvariable=self.port_var)
        self.port.pack(side=LEFT)
        self.upnp_var = IntVar()
        self.cb_upnp = Checkbutton(text='use UPnP', variable=self.upnp_var)
        self.cb_upnp.pack(side=LEFT)
        self.cb_upnp['state'] = 'disabled'
        self.stream_type = IntVar()
        self.stream_type.set(2)
        self.rb_public = Radiobutton(text="public", variable=self.stream_type, value=1)
        self.rb_public.pack(side=LEFT)
        self.rb_private = Radiobutton(text="private", variable=self.stream_type, value=2)
        self.rb_private.pack(side=LEFT)
        self.rb_offline = Radiobutton(text="offline", variable=self.stream_type, value=3)
        self.rb_offline.pack(side=LEFT)
        self.b_start = Button(text="start", command=self.start_server)
        self.b_start.pack(side=RIGHT)
    
    def main(self):
        self.running_gui = True
        self.window.mainloop()
        self.running_gui = False
        self.run_miniserver = False
        self.quit = True
    
    def close_event(self):
        self.run_miniserver = False
        self.quit = True
        self.log_mode()
        if self.running_streamchek:
            self.write_to_log("Stream checker running!\n")
            self.window.after(1000, self.close_event)
        elif self.running_miniserver:
            self.write_to_log("Mini-server running!\n")
            try:
                # forces mini server to stop
                response = urllib2.urlopen('http://localhost:' + str(self.get_port()), timeout=1)
            except:
                self.write_to_log("Can't contact mini-server!\n")
            self.window.after(1000, self.close_event)
        else:
            self.window.destroy()
    
    def write_to_log(self, text):
        self.textlog['state'] = 'normal'
        self.textlog.insert(END, text)
        self.textlog.yview(END)
        self.textlog['state'] = 'disabled'
    
    def set_port(self, port):
        self.port.delete(0, END)
        self.port.insert(0, port)
    
    def get_port(self):
        try:
            return int( self.port.get() )
        except:
            return 0
    
    def enable_upnp(self):
        self.cb_upnp['state'] = 'normal'
    
    def set_active_upnp(self, value=False):
        if value:
            self.cb_upnp.select()
        else:
            self.cb_upnp.deselect()
    
    def is_upnp_active(self):
        return self.upnp_var.get() == 1
    
    def is_public(self):
        return self.stream_type.get() == 1
    
    def is_offline(self):
        return self.stream_type.get() == 3
    
    def log_mode(self):
        self.port['state'] = 'disabled'
        self.cb_upnp['state'] = 'disabled'
        self.rb_public['state'] = 'disabled'
        self.rb_private['state'] = 'disabled'
        self.rb_offline['state'] = 'disabled'
        self.b_start['state'] = 'disabled'
    
    def show_views(self):
        self.label_views['text'] = str(self.get_views())+' views '
    
    def show_link(self, streamid='', key=''):
        self.streamid = streamid
        self.key = key
        if streamid == '' or key == '': #offline
            self.b_link['text'] = 'http://localhost:'+str(self.get_port())
            self.b_link['state'] = 'normal'
            self.open_link()
        else:
            self.b_link['text'] = self.get_pystream_url() + '/s/' + self.streamid
            self.b_link['state'] = 'normal'
            self.open_link()
        self.b_link.pack(side=LEFT, expand=True, fill=BOTH)
        self.label_views.pack(side=RIGHT)
    
    def open_link(self):
        if self.streamid == '' or self.key == '': #offline
            webbrowser.open('http://localhost:'+str(self.get_port()))
        else:
            webbrowser.open(self.get_pystream_url() + '/s/' + self.streamid + '?key=' + self.key)
    
    def retry_share(self):
        self.b_start['state'] = 'normal'
    
    def start_server(self):
        self.folder = tkFileDialog.askdirectory(initialdir="/", title='Please select a folder to share')
        self.run_miniserver = True


if __name__ == "__main__":
    gui = Pystream_tk()
    server = Mini_server( gui )
    stream_checker = Stream_checker( gui )
    server.start()
    stream_checker.start()
    gui.main()
