#!/usr/bin/env python

import cgi, os

# cargamos django 1.2
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')
from google.appengine.ext.webapp import template

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from base import *


class Main_page(webapp.RequestHandler):
    def get(self):
        template_values = {
            'title': 'pyStream - alpha',
            'description': 'Data sharing made easy.',
            'tags': 'share, folder, python, linux, ubuntu',
            'streams': db.GqlQuery("SELECT * FROM Stream ORDER BY date DESC").fetch(20),
            'reports': db.GqlQuery("SELECT * FROM Report ORDER BY date ASC").fetch(20),
            'logout': users.create_logout_url('/')
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/admin.html')
        self.response.out.write( template.render(path, template_values) )


def main():
    application = webapp.WSGIApplication([('/admin/', Main_page),
                                         ],
                                         debug=DEBUG_FLAG)
    webapp.template.register_template_library('filters.django_filters')
    run_wsgi_app(application)


if __name__ == "__main__":
    main()

