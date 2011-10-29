#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of Pystream
# Copyright (C) 2011  Carlos Garcia Gomez  admin@pystream.com
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

DEBUG_FLAG = True
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''
PYSTREAM_VERSION = '4'
PYSTREAM_URL = 'http://www.pystream.com'
WINDOWS_CLIENT_URL = '/download'
LINUX_CLIENT_URL = 'https://github.com/downloads/NeoRazorX/pystream/pst-linux.tar.bz2'
MAC_CLIENT_URL = '/download'

import logging, datetime, random, re, urllib
from google.appengine.ext import webapp, db, search
from google.appengine.api import memcache

class Basic_tools:
    def is_ip6(self, ip):
        pattern = re.compile(r'(?:(?<=::)|(?<!::):)', re.VERBOSE | re.IGNORECASE | re.DOTALL)
        return pattern.match(ip) is not None
    
    def get_os(self, data):
        os = 'unknown'
        for aux in ['mac', 'iphone', 'ipad', 'ipod', 'windows', 'linux', 'android']:
            if data.lower().find( aux ) != -1:
                os = aux
        return os
    
    def streams_from_ip(self, ip):
        ss = db.GqlQuery("SELECT * FROM Stream WHERE ip = :1", ip).fetch(100)
        if ss:
            local_ss = []
            # selecting non-fake streams
            for s in ss:
                if not s.is_fake() and not s.is_closed():
                    local_ss.append(s)
            # date order
            finalmix = []
            while len(local_ss) > 0:
                elem = None
                for m in local_ss:
                    if not elem:
                        elem = m
                    elif m.date > elem.date:
                        elem = m
                finalmix.append(elem)
                local_ss.remove(elem)
            return finalmix
        else:
            return []
    
    def valid_tag_name(self, tag):
        return tag.strip().lower().replace('%20', '_').replace('%2B', '_').replace('+', '_').replace(' ', '_')
    
    def tags2cache(self, tags, all_tags = None):
        if tags:
            # first check because may be not provided
            if all_tags is None:
                all_tags = memcache.get('previous_searches')
            if all_tags is None:
                all_tags = []
                for tag in tags:
                    if len(tag) > 1:
                        all_tags.append([self.valid_tag_name(tag), 0])
                memcache.add('previous_searches', all_tags)
            else:
                for ntag in tags:
                    found = False
                    for otag in all_tags:
                        if self.valid_tag_name(ntag) == otag[0]:
                            found = True
                    if not found and len(ntag) > 1:
                        all_tags.append([self.valid_tag_name(ntag), 0])
                memcache.replace('previous_searches', all_tags)
            return all_tags
        else:
            return []
    
    def page2search(self, link, text, page_type, date, all_tags = None):
        if all_tags is None:
            all_tags = memcache.get('previous_searches')
        found_tags = []
        if link != '' and text != '' and all_tags is not None:
            logging.info('Searching tags for link: ' + link)
            for tag in all_tags:
                if re.search('\\b'+tag[0]+'\\b', text.lower()) or re.search('\\b'+tag[0].replace('_', ' ')+'\\b', text.lower()):
                    found_tags.append(tag[0])
                    logging.info('Link: ' + link + ' found tag: ' + tag[0])
                    tag_links = memcache.get('search_' + tag[0])
                    if len(text) > 200:
                        element = [link, page_type, date, text[:200]+'...']
                    else:
                        element = [link, page_type, date, text]
                    if tag_links is None:
                        memcache.add('search_' + tag[0], [element])
                    else:
                        found = False
                        for ele in tag_links:
                            if element[0] == ele[0]:
                                ele[3] = element[3]
                                found = True
                        if not found:
                            tag_links.append(element)
                        memcache.replace('search_' + tag[0], tag_links)
        return found_tags
    
    def search_job(self, all_tags = None):
        if all_tags is None:
            all_tags = memcache.get('previous_searches')
        if random.randint(0, 3) > 0:
            query = db.GqlQuery("SELECT * FROM Stream")
            streams = query.fetch(20, random.randint(0, max(0, query.count()-20)))
            for s in streams:
                if s.is_public():
                    self.tags2cache(s.tags, all_tags)
                    new_tags = self.page2search(s.get_link(), s.description, 'stream', s.date, all_tags)
                    if s.tags != new_tags:
                        try:
                            s.tags = new_tags
                            s.put()
                        except:
                            pass
        else:
            query = db.GqlQuery("SELECT * FROM Request")
            requests = query.fetch(20, random.randint(0, max(0, query.count()-20)))
            for r in requests:
                self.tags2cache(r.tags, all_tags)
                new_tags = self.page2search(r.get_link(), r.description, 'request', r.date, all_tags)
                if r.tags != new_tags:
                    try:
                        r.tags = new_tags
                        r.put()
                    except:
                        pass
    
    def search_pylink_file_name(self, query):
        if query:
            return db.GqlQuery("SELECT * FROM Pylink WHERE file_name = :1", query).fetch(100)
        else:
            return None
    
    def search(self, query=''):
        if len(query) > 1:
            stats = Stat_cache()
            stats.put_search(query)
            self.search_job( stats.get_searches() )
            mix = memcache.get('search_' + query.lower())
            if mix is not None:
                finalmix = []
                while len(mix) > 0:
                    elem = None
                    for m in mix:
                        if not elem:
                            elem = m
                        elif m[2] > elem[2]:
                            elem = m
                    finalmix.append(elem)
                    mix.remove(elem)
                return finalmix
            else:
                return []
        else:
            return []
    
    def unique_links(self, links):
        ulinks = []
        for link in links:
            if link not in ulinks:
                ulinks.append(link)
        return ulinks
    
    def txt2links(self, txt):
        links = []
        aux_links = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', txt)
        for link in aux_links:
            if link not in links:
                links.append(link)
        aux_links = re.findall(r'/api/redir/[0-9]+/.+', txt)
        for link in aux_links:
            if link not in links:
                links.append(link)
        return links
    
    def new_pylinks(self, links, origin):
        all_links = []
        if len(links) > 0 and origin:
            while len(links) > 0:
                check_links = []
                while len(links) > 0 and len(check_links) < 25:
                    check_links.append( links[0] )
                    links.remove( links[0] )
                olinks = db.GqlQuery("SELECT * FROM Pylink WHERE url in :1", check_links).fetch(25)
                for l in check_links:
                    encontrado = False
                    if olinks:
                        for o in olinks:
                            if o.url == l:
                                encontrado = True
                                if origin not in o.origin:
                                    aux_origin = o.origin
                                    aux_origin.append(origin)
                                    o.origin = aux_origin
                                    o.put()
                                all_links.append( o.key() )
                    if not encontrado:
                        pyl = Pylink()
                        pyl.url = l
                        pyl.origin = [origin]
                        if pyl.url[:11] == '/api/redir/':
                            pyl.file_name = urllib.unquote(pyl.url).rpartition('/')[2]
                            pyl.status = 3
                        pyl.put()
                        all_links.append( pyl.key() )
        return all_links
    
    def get_random_password(self):
        return str( random.randint(0, 999999) )


class Basic_page(webapp.RequestHandler):
    def get_lang(self):
        try:
            if self.request.environ['HTTP_ACCEPT_LANGUAGE'].lower().find('es') != -1:
                return 'es'
            else:
                return 'en'
        except:
            return 'en'


class Stat_cache(Basic_tools):
    def __init__(self):
        self.downloads = memcache.get('all_downloads')
        self.machines = memcache.get('all_pystream_machines')
        self.searches = memcache.get('previous_searches')
        self.pages = memcache.get('new_pages')
    
    def put_download(self, os):
        if self.downloads is None:
            self.downloads = {
                'windows': 0,
                'linux': 0,
                'mac': 0,
                'unknown': 0
            }
            is_cached = False
        else:
            is_cached = True
        if os in ['windows', 'linux', 'mac']:
            self.downloads[os] += 1
        else:
            self.downloads['unknown'] += 1
        if is_cached:
            memcache.replace('all_downloads', self.downloads)
        else:
            memcache.add('all_downloads', self.downloads)
    
    def put_machine(self, machine, ip6 = False, upnp = False):
        if machine != '':
            os = 'unknown'
            for aux in ['bsd', 'darwin', 'mac', 'iphone', 'ipad', 'ipod', 'windows', 'linux', 'android']:
                if machine.lower().find( aux ) != -1:
                    os = aux
            if self.machines is None:
                self.machines = [[os, 1, 0, 0, 0]]
                if ip6:
                    self.machines[0][2] += 1
                elif upnp:
                    self.machines[0][3] += 1
                memcache.add('all_pystream_machines', self.machines)
            else:
                found = False
                for m in self.machines:
                    if m[0] == os:
                        m[1] += 1
                        if ip6:
                            m[2] += 1
                        elif upnp:
                            m[3] += 1
                        found = True
                if not found:
                    self.machines = [[os, 1, 0, 0, 0]]
                    if ip6:
                        self.machines[0][2] += 1
                    elif upnp:
                        self.machines[0][3] += 1
                memcache.replace('all_pystream_machines', self.machines)
    
    def put_firewalled_machine(self, machine):
        if machine != '':
            os = 'unknown'
            for aux in ['bsd', 'darwin', 'mac', 'iphone', 'ipad', 'ipod', 'windows', 'linux', 'android']:
                if machine.lower().find( aux ) != -1:
                    os = aux
            if self.machines is None:
                self.machines = [[os, 1, 0, 0, 1]]
                memcache.add('all_pystream_machines', self.machines)
            else:
                found = False
                for m in self.machines:
                    if m[0] == os:
                        m[4] += 1
                        found = True
                if not found:
                    self.machines = [[os, 1, 0, 0, 1]]
                memcache.replace('all_pystream_machines', self.machines)
    
    def put_search(self, query=''):
        if len(query) > 1:
            found = False
            if self.searches is None:
                self.searches = [[query.lower(), 1]]
                memcache.add('previous_searches', self.searches)
            else:
                for s in self.searches:
                    if s[0] == self.valid_tag_name(query):
                        s[1] += 1
                        found = True
                if not found:
                    self.searches.append([self.valid_tag_name(query), 1])
                # short
                if self.searches:
                    aux = []
                    elem = None
                    while self.searches != []:
                        for s in self.searches:
                            if not elem:
                                elem = s
                            elif s[1] > elem[1]:
                                elem = s
                        aux.append(elem)
                        self.searches.remove(elem)
                        elem = None
                    self.searches = aux
                memcache.replace('previous_searches', self.searches)
    
    def put_page(self, page_type, num=1):
        if self.pages is None:
            is_cached = False
            self.pages = {
                'streams': 0,
                'requests': 0,
                'comments': 0,
                'pylinks': 0
            }
        else:
            is_cached = True
        if page_type == 'stream':
            self.pages['streams'] += num
            memcache.delete('random_pages')
        elif page_type == 'request':
            self.pages['requests'] += num
            memcache.delete('random_pages')
        elif page_type == 'comment':
            self.pages['comments'] += num
        elif page_type == 'pylinks':
            self.pages['pylinks'] += num
        else:
            logging.warning('Unknown page type!')
        if is_cached:
            memcache.replace('new_pages', self.pages)
        else:
            memcache.add('new_pages', self.pages)
    
    def get_downloads(self):
        return self.downloads
    
    def get_machines(self):
        return self.machines
    
    def get_searches(self):
        return self.searches
    
    def get_pages(self):
        return self.pages
    
    def get_summary(self):
        total_downloads = 0
        if self.downloads:
            for d in self.downloads.values():
                total_downloads += d
        total_machines = total_machines_ip6 = total_machines_upnp = total_machines_firewalled = 0
        if self.machines:
            for m in self.machines:
                total_machines += m[1]
                total_machines_ip6 += m[2]
                total_machines_upnp += m[3]
                total_machines_firewalled += m[4]
        total_searches = 0
        if self.searches:
            for s in self.searches:
                total_searches += s[1]
        total_streams = 0
        total_requests = 0
        total_comments = 0
        total_pylinks = 0
        if self.pages:
            total_streams = self.pages['streams']
            total_requests = self.pages['requests']
            total_comments = self.pages['comments']
            total_pylinks = self.pages['pylinks']
        summary = {
            'downloads': total_downloads,
            'machines': total_machines,
            'ip6': total_machines_ip6,
            'upnp': total_machines_upnp,
            'upnp': total_machines_firewalled,
            'searches': total_searches,
            'streams': total_streams,
            'requests': total_requests,
            'comments': total_comments,
            'pylinks': total_pylinks
        }
        return summary


class Stream(db.Model, Basic_tools):
    access_pass = db.StringProperty(default='')
    alive = db.DateTimeProperty(auto_now_add=True)
    comments = db.IntegerProperty(default=0)
    date = db.DateTimeProperty(auto_now_add=True)
    description = db.TextProperty()
    edit_pass = db.StringProperty(default='')
    ip = db.StringProperty()
    lan_ip = db.StringProperty()
    os = db.StringProperty(default='unknown')
    pylinks = db.ListProperty( db.Key )
    port = db.IntegerProperty(default=8081)
    size = db.IntegerProperty(default=0)
    # status:
    # 0 -> default
    # 1 -> public ip6
    # 2 -> private ip6
    # 3 -> private passw. protected ip6
    # 11 -> public ip4
    # 12 -> private ip4
    # 13 -> private passw. protected ip4
    # 91 -> public fake
    # 92 -> private fake
    # 93 -> private passw. protected fake
    # 100 -> closed
    # 101 -> error
    status = db.IntegerProperty(default=0)
    tags = db.StringListProperty()
    
    def get_link(self):
        if self.status in [3, 13, 93]: # password protected stream
            return '/ps/' + str( self.key().id() )
        else:
            return '/s/' + str( self.key().id() )
    
    def get_comments(self):
        comments = memcache.get('comments_' + str(self.key()))
        if comments is None:
            query = db.GqlQuery("SELECT * FROM Comment WHERE origin = :1 ORDER BY date ASC",
                                self.get_link() )
            numc = query.count()
            comments = query.fetch(numc)
            if self.comments != numc:
                self.comments = numc
                try:
                    self.put()
                except:
                    logging.warning('Cant update the number of comments on stream!')
            if not memcache.add('comments_' + str(self.key()), comments):
                logging.warning("Error adding comments to memcache!")
        return comments
    
    def get_pylinks(self):
        links = memcache.get('pylinks_' + self.get_link())
        if links is None:
            links = []
            num = 0
            while num < len(self.pylinks):
                pyl = Pylink.get( self.pylinks[num] )
                if pyl:
                    links.append( pyl )
                    num += 1
                else:
                    aux_pylinks = self.pylinks
                    aux_pylinks.remove( self.pylinks[num] )
                    self.pylinks = aux_pylinks
                    try:
                        self.put()
                    except:
                        logging.warning("Can't fix stream's pylinks!")
            # shorting
            aux = []
            while len(links) > 0:
                selection = links[0]
                for l in links:
                    if l.file_name < selection.file_name:
                        selection = l
                aux.append(selection)
                links.remove(selection)
            links = aux
            if not memcache.add('pylinks_' + self.get_link(), links):
                logging.warning("Error adding pylinks to memcache!")
        return links
    
    def add_links(self, links):
        old_links = self.get_pylinks()
        new_links = []
        for link in links:
            if link not in old_links:
                new_links.append(link)
        new_link_keys = self.new_pylinks(new_links, self.get_link())
        link_keys = self.pylinks
        for k in new_link_keys:
            link_keys.append(k)
        self.pylinks = link_keys
    
    def status_text(self):
        if self.status == 0:
            return 'uninitielized'
        elif self.status == 1:
            return 'public ip6'
        elif self.status == 2:
            return 'private ip6'
        elif self.status == 3:
            return 'private passw. protected ip6'
        elif self.status == 11:
            return 'public ip4'
        elif self.status == 12:
            return 'private ip4'
        elif self.status == 13:
            return 'private passw. protected ip4'
        elif self.status == 91:
            return 'public fake'
        elif self.status == 92:
            return 'private fake'
        elif self.status == 93:
            return 'private passw. protected fake'
        elif self.status == 100:
            return 'closed'
        elif self.status == 101:
            return 'error'
        else:
            return 'unknown'
    
    def is_public(self):
        if self.status in [1, 11, 91]:
            return True
        else:
            return False
    
    def is_fake(self):
        if self.status in [91, 92, 93]:
            return True
        else:
            return False
    
    def is_closed(self):
        if self.status >= 100:
            return True
        else:
            return False
    
    def need_password(self):
        if self.status in [3, 13, 93]:
            return True
        else:
            return False
    
    def set_public(self):
        if self.status in [1, 2, 3]:
            self.status = 1
        elif self.status in [11, 12, 13]:
            self.status = 11
        else:
            self.status = 91
    
    def set_private(self):
        if self.status in [1, 2, 3]:
            self.status = 2
        elif self.status in [11, 12, 13]:
            self.status = 12
        else:
            self.status = 92
    
    def set_private_passw(self):
        if self.status in [1, 2, 3]:
            self.status = 3
        elif self.status in [11, 12, 13]:
            self.status = 13
        else:
            self.status = 93
    
    def rm_comments(self):
        db.delete( Comment.all().filter('origin = ', self.get_link()) )
    
    def rm_pylinks(self):
        for pyl in self.get_pylinks():
            if pyl.origin == [self.get_link()]:
                logging.info('Removing pylink: ' + pyl.url)
                db.delete(pyl)
    
    def rm_cache(self):
        memcache.delete_multi(['comments_'+str(self.key()), 'pylinks_'+self.get_link(), 'random_pages'])
    
    def rm_all(self):
        self.rm_comments()
        self.rm_pylinks()
        self.rm_cache()
        db.delete( self.key() )


class Request(db.Model):
    checked = db.BooleanProperty(default=False)
    comments = db.IntegerProperty(default=0)
    date = db.DateTimeProperty(auto_now_add=True)
    description = db.TextProperty()
    edit_pass = db.StringProperty(default='')
    email = db.EmailProperty()
    ip = db.StringProperty()
    os = db.StringProperty(default='unknown')
    tags = db.StringListProperty()
    
    def get_link(self):
        return '/r/' + str( self.key().id() )
    
    def get_comments(self):
        comments = memcache.get('comments_' + str(self.key()))
        if comments is None:
            query = db.GqlQuery("SELECT * FROM Comment WHERE origin = :1 ORDER BY date ASC",
                                self.get_link() )
            numc = query.count()
            comments = query.fetch(numc)
            if self.comments != numc:
                self.comments = numc
                try:
                    self.put()
                except:
                    logging.warning('Cant update the number of comments on request!')
            if not memcache.add('comments_' + str(self.key()), comments):
                logging.warning("Error adding comments to memcache!")
        return comments
    
    def rm_comments(self):
        db.delete( Comment.all().filter('origin = ', self.get_link()) )
    
    def rm_cache(self):
        memcache.delete_multi(['comments_' + str(self.key()), 'random_pages'])
    
    def rm_all(self):
        self.rm_comments()
        self.rm_cache()
        db.delete( self.key() )


class Comment(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    ip = db.StringProperty()
    os = db.StringProperty(default='unknown')
    origin = db.StringProperty()
    text = db.TextProperty()
    
    def get_origin(self):
        try:
            if self.origin[:3] == '/s/':
                return Stream.get_by_id( int(self.origin[3:]) )
            elif self.origin[:4] == '/ps/':
                return Stream.get_by_id( int(self.origin[4:]) )
            elif self.origin[:3] == '/r/':
                return Request.get_by_id( int(self.origin[3:]) )
            else:
                return None
        except:
            return None
    
    def get_link(self):
        return self.origin + '#' + str(self.key())


class Pylink(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    file_name = db.StringProperty()
    origin = db.StringListProperty()
    # status:
    # 0 = unknown
    # 1 = online
    # 2 = offline
    # 3 = no need to check
    status = db.IntegerProperty(default=0)
    url = db.StringProperty()
    
    def get_status(self):
        if self.status == 0:
            return 'unknown'
        elif self.status == 1:
            return 'online'
        elif self.status == 2:
            return 'offline'
        elif self.status == 3:
            return 'no need to check'
        else:
            return 'error'
    
    def get_status_html(self):
        if self.status == 0:
            return '<span class="yellow">unknown</span>'
        elif self.status == 1:
            return '<span class="green">online</span>'
        elif self.status == 2:
            return '<span class="red">offline</span>'
        elif self.status == 3:
            return '<span class="green">&nbsp;</span>'
        else:
            return '<span class="yellow">error</span>'
    
    def get_file_name(self):
        if self.file_name is not None:
            return self.file_name
        else:
            return ''
    
    def rm_cache(self):
        for ori in self.origin:
            memcache.delete('pylinks_'+ori)


class Report(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    ip = db.StringProperty()
    link = db.StringProperty(default='/')
    os = db.StringProperty(default='unknown')
    text = db.TextProperty()
    
    def get_link(self):
        return self.link


class Stat_item(db.Model):
    comments = db.IntegerProperty(default=0)
    date = db.DateTimeProperty(auto_now_add=True)
    downloads = db.IntegerProperty(default=0)
    ip6 = db.IntegerProperty(default=0)
    upnp = db.IntegerProperty(default=0)
    machines = db.IntegerProperty(default=0)
    pylinks = db.IntegerProperty(default=0)
    reports = db.IntegerProperty(default=0)
    requests = db.IntegerProperty(default=0)
    searches = db.IntegerProperty(default=0)
    streams = db.IntegerProperty(default=0)
    
    def ip6_relation(self):
        if self.machines > 0 and self.ip6 > 0:
            return (self.ip6*100)/self.machines
        else:
            return 0
    
    def upnp_relation(self):
        if self.machines > 0 and self.upnp > 0:
            return (self.upnp*100)/self.machines
        else:
            return 0
