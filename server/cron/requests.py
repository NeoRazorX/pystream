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

import logging
from google.appengine.ext import db
from google.appengine.api import mail
from base import *

class Request_checker():
    def __init__(self):
        rs = db.GqlQuery("SELECT * FROM Request WHERE checked = :1", False).fetch(10)
        if rs:
            for r in rs:
                if r.email not in ['', 'fuck@you.com']:
                    subject = 'Pystream notification'
                    body = 'Hello! Your request is ready here: '
                    body += PYSTREAM_URL + r.get_link() + "\n"
                    body += 'Your edition password is: ' + r.edit_pass + "\n"
                    body += 'Have a nice day!'
                    try:
                        mail.send_mail("admin@pystream.com", r.email, subject, body)
                        logging.info('Send mail to: ' + r.email)
                        logging.info(body)
                        r.checked = True
                        r.put()
                    except:
                        logging.warning('Error sending mail to: ' + r.email)
                        logging.info(body)
        else:
            logging.info('No requests to check :-)')


if __name__ == "__main__":
    Request_checker()
