#!/usr/bin/env python

import cgi, os, math

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
            'stats': self.get_stats(),
            'logout': users.create_logout_url('/'),
            'admin': users.is_current_user_admin()
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/admin.html')
        self.response.out.write( template.render(path, template_values) )
    
    def get_stats(self):
        sts = db.GqlQuery("SELECT * FROM Stat_item ORDER BY date DESC").fetch(1)
        if sts:
            return sts[0]
        else:
            return None


class Streams_page(webapp.RequestHandler):
    def get(self):
        removed = self.remove_stream( self.request.get('rm') )
        ss,pages_data = self.get_streams(self.request.get('p'), 25)
        template_values = {
            'title': 'pyStream - alpha',
            'description': 'Data sharing made easy.',
            'tags': 'share, folder, python, linux, ubuntu',
            'streams': ss,
            'removed': removed,
            'pages_data': pages_data,
            'logout': users.create_logout_url('/'),
            'admin': users.is_current_user_admin()
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/admin_streams.html')
        self.response.out.write( template.render(path, template_values) )
    
    def get_streams(self, p=0, l=10):
        ss = None
        pages = total = 0
        query = db.GqlQuery("SELECT * FROM Stream ORDER BY date DESC")
        total = query.count()
        pages = int( math.ceil( total / float(l) ) )
        try:
            current = int(p)
            if current < 0:
                current = 0
        except:
            current = 0
        ss = query.fetch(l, l*current)
        return ss,['/admin/streams?p=', total, pages, current]
    
    def remove_stream(self, key):
        done = False
        if key:
            try:
                s = Stream.get( key )
                s.rm_all()
                s.delete()
                done = True
            except:
                logging.error('Fail to remove stream!')
        return done


class Reports_page(webapp.RequestHandler):
    def get(self):
        removed = self.remove_report( self.request.get('rm') )
        rr,pages_data = self.get_reports(self.request.get('p'), 25)
        template_values = {
            'title': 'pyStream - alpha',
            'description': 'Data sharing made easy.',
            'tags': 'share, folder, python, linux, ubuntu',
            'reports': rr,
            'removed': removed,
            'pages_data': pages_data,
            'logout': users.create_logout_url('/'),
            'admin': users.is_current_user_admin()
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/admin_reports.html')
        self.response.out.write( template.render(path, template_values) )
    
    def get_reports(self, p=0, l=10):
        ss = None
        pages = total = 0
        query = db.GqlQuery("SELECT * FROM Report ORDER BY date DESC")
        total = query.count()
        pages = int( math.ceil( total / float(l) ) )
        try:
            current = int(p)
            if current < 0:
                current = 0
        except:
            current = 0
        ss = query.fetch(l, l*current)
        return ss,['/admin/reports?p=', total, pages, current]
    
    def remove_report(self, key):
        done = False
        if key:
            try:
                r = Report.get( key )
                r.delete()
                done = True
            except:
                logging.error("Can't remove report: " + str(key) )
        return done


class Stats_page(webapp.RequestHandler):
    def get(self):
        sts,pages_data = self.get_stats()
        template_values = {
            'title': 'pyStream - alpha',
            'description': 'Data sharing made easy.',
            'tags': 'share, folder, python, linux, ubuntu',
            'stats': sts,
            'pages_data': pages_data,
            'logout': users.create_logout_url('/'),
            'admin': users.is_current_user_admin()
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/admin_stats.html')
        self.response.out.write( template.render(path, template_values) )
    
    def get_stats(self, p=0, l=10):
        ss = None
        pages = total = 0
        query = db.GqlQuery("SELECT * FROM Stat_item ORDER BY date DESC")
        total = query.count()
        pages = int( math.ceil( total / float(l) ) )
        try:
            current = int(p)
            if current < 0:
                current = 0
        except:
            current = 0
        ss = query.fetch(l, l*current)
        return ss,['/admin/stats?p=', total, pages, current]


def main():
    application = webapp.WSGIApplication([('/admin/', Main_page),
                                          ('/admin/streams', Streams_page),
                                          ('/admin/reports', Reports_page),
                                          ('/admin/stats', Stats_page)],
                                         debug=DEBUG_FLAG)
    webapp.template.register_template_library('filters.django_filters')
    run_wsgi_app(application)


if __name__ == "__main__":
    main()

