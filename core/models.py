__author__ = 'shivnarayan'
import json

import settings
from mongoengine import *
connect('test',host = settings.MONGO_HOST, port = settings.MONGO_PORT)

class RootDocument(Document):
    title                    =  StringField(required = False,db_field = 't')
    link                     =  StringField(required = False,db_field = 'l')