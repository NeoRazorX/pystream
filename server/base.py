#!/usr/bin/env python

DEBUG_FLAG = True

from google.appengine.ext import db

class Stream(db.Model):
    ip = db.IntegerProperty(default=0)
    port = db.IntegerProperty(default=0)
    date = db.DateTimeProperty(auto_now_add=True)

