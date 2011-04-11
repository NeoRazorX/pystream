#!/usr/bin/env python

import cgi, os

# cargamos django 1.2
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')
from google.appengine.ext.webapp import template

from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users

from base import *

class Portada(webapp.RequestHandler):
    def get(self):
        
        template_values = {
            'titulo': 'pyStream - beta',
            'descripcion': 'Folder sharing made easy.',
            'tags': 'share, folder, python, linux, ubuntu'
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/portada.html')
        self.response.out.write( template.render(path, template_values) )

def main():
    application = webapp.WSGIApplication([('/', Portada),
                                    ],
                                    debug=DEBUG_FLAG)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

