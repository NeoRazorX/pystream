#!/usr/bin/env python
#
# Author: Carlos Garcia Gomez
# Date: April 11, 2011
# web: http://www.pystream.com

from pystream import *

try:
    import webbrowser
    from Tkinter import *
except Exception,e:
	print 'Lost dependency:', e
	sys.exit(1)


class Pystream_tk(Mini_gui):
    def __init__(self):
        Mini_gui.__init__(self)
        self.label = Label(text='Caca').pack(expand=YES, fill=BOTH)
        self.quit = True
    
    def main(self):
        mainloop()
    
    def write_to_log(self, text):
        print text
    
    def set_port(self, port):
        pass
    
    def get_port(self):
        return 0
    
    def enable_upnp(self):
        pass
    
    def set_active_upnp(self, value=False):
        pass
    
    def is_upnp_avaliable(self):
        return False
    
    def is_public(self):
        pass
    
    def select_folder(self):
        pass
    
    def get_folder(self):
        return False
    
    def log_mode(self):
        pass
    
    def show_link(self, streamid, key):
        webbrowser.open(self.PYSTREAM_URL + '/s/' + streamid + '?key=' + key)
    
    def retry_share(self):
        pass


if __name__ == "__main__":
    gui = Pystream_tk()
    server = Mini_server( gui )
    server.start()
    gui.main()

