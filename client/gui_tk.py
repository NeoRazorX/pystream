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

from pystream import *

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
        self.folder = ''
        self.window = Tk()
        self.window.protocol("WM_DELETE_WINDOW", self.close_event)
        self.window.title('Pystream client')
        self.window.iconbitmap('@icon.xbm')
        self.window.minsize(500,400)
        self.textlog = Text()
        self.textlog.pack(expand=True, fill=BOTH)
        self.textlog['state'] = 'disabled'
        laberport = Label(text='Port:')
        laberport.pack(side=LEFT)
        self.port_var = StringVar()
        self.port = Spinbox(width=4, from_=6000, to=9000, textvariable=self.port_var)
        self.port.pack(side=LEFT)
        self.upnp_var = IntVar()
        self.cb_upnp = Checkbutton(text='use UPnP', variable=self.upnp_var)
        self.cb_upnp.pack(side=LEFT)
        self.cb_upnp['state'] = 'disabled'
        self.public_var = IntVar()
        self.cb_public = Checkbutton(text='public', variable=self.public_var)
        self.cb_public.pack(side=LEFT)
        self.cb_public.select()
        self.b_start = Button(text="Start sharing!", command=self.start_server)
        self.b_start.pack(side=RIGHT)
    
    def main(self):
        self.window.mainloop()
        self.run_miniserver = False
        self.quit = True
    
    def close_event(self):
        self.run_miniserver = False
        self.quit = True
        if self.running_streamchek:
            self.write_to_log("Stream checker running!\n")
            self.window.after(1000, self.close_event)
        elif self.running_miniserver:
            self.write_to_log("Mini-server running!\n")
            try:
                # forces mini server to stop
                response = urllib2.urlopen('http://localhost:' + str(self.get_port()), timeout=2)
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
    
    def is_upnp_avaliable(self):
        return self.upnp_var.get() == 1
    
    def is_public(self):
        return self.public_var.get() == 1
    
    def select_folder(self):
        self.write_to_log("Press start button to select folder and start sharing.\n")
    
    def get_folder(self):
        return self.folder
    
    def log_mode(self):
        self.port['state'] = 'disabled'
        self.cb_upnp['state'] = 'disabled'
        self.cb_public['state'] = 'disabled'
        self.b_start['state'] = 'disabled'
    
    def show_link(self, streamid, key):
        webbrowser.open(self.PYSTREAM_URL + '/s/' + streamid + '?key=' + key)
    
    def retry_share(self):
        self.b_start['state'] = 'normal'
    
    def start_server(self):
        self.folder = tkFileDialog.askdirectory(initialdir="/", title='Please select a folder to share')
        self.run_miniserver = True


if __name__ == "__main__":
    gui = Pystream_tk()
    server = Mini_server( gui )
    server.start()
    stream_checker = Stream_checker( gui )
    stream_checker.start()
    gui.main()
    while stream_checker.is_alive():
        print 'stream_checker alive!'
        time.sleep(1)
    while server.is_alive():
        print 'mini-server alive!'
        time.sleep(1)

