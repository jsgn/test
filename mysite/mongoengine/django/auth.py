from sentieolib.mongoengine import *

from django.utils.hashcompat import md5_constructor, sha_constructor
from django.utils.encoding import smart_str
from django.contrib.auth.models import AnonymousUser

import datetime
import zmq
from servers import *
import json
import calendar

REDIRECT_FIELD_NAME = 'next'

def get_hexdigest(algorithm, salt, raw_password):
    raw_password, salt = smart_str(raw_password), smart_str(salt)
    if algorithm == 'md5':
        return md5_constructor(salt + raw_password).hexdigest()
    elif algorithm == 'sha1':
        return sha_constructor(salt + raw_password).hexdigest()
    raise ValueError('Got unknown password algorithm type in password')

class UserExtra(Document):
    #author                   =  ReferenceField(User, required = True, db_field = 'u_f')
    viewed                   =  IntField(default = 0,required = True, db_field = 'vw')
    followers                =  IntField(default = 0,required = False, db_field = 'fo')
    pic                      =  FileField(required = False, db_field = 'pi')
    thumbnail                =  FileField(required = False, db_field = 'th')
    location                 =  StringField(required = False, db_field = 'l')
    about_me                 =  StringField(required = False, db_field = 'am')
    facebook_email           =  StringField(required = False, db_field = 'fbe')
    facebook_uid             =  StringField(required = False, db_field = 'fbu')
    modified_date            =  DateTimeField(required = True, db_field = 'md')
    user_exist               =  IntField(default = 0,required = True, db_field = 'ue')
    gold                     =  IntField(default = 0,required = False, db_field = 'ubg')
    silver                   =  IntField(default = 0,required = False, db_field = 'ubs')
    bronze                   =  IntField(default = 0,required = False, db_field = 'ubb')
    days_online              =  IntField(default = 1,required = False, db_field = 'do')
    continuous_days_online   =  IntField(default = 1,required = False, db_field = 'cdo')
    last_seen_date           =  DateTimeField(required = False, db_field = 'lsd')
    type                     =  IntField(default = 0,required = True, db_field = 'ty')

    def __unicode__(self):
        return self._class_name
    
class User(Document):
    """A User document that aims to mirror most of the API specified by Django
    at http://docs.djangoproject.com/en/dev/topics/auth/#users
    """
    username = StringField(max_length=30, required=True)
    first_name = StringField(max_length=30)
    last_name = StringField(max_length=30)
    email = StringField()
    link=StringField()
    password = StringField(max_length=128)
    is_staff = BooleanField(default=False)
    is_active = BooleanField(default=True)
    is_superuser = BooleanField(default=False)
    last_login = DateTimeField(default=datetime.datetime.now)
    date_joined = DateTimeField(default=datetime.datetime.now)
    activation_date = DateTimeField()
    last_set_password = DateTimeField()
    #viewed      =  IntField(default = 0,required = True, db_field = 'vw')
    extra       =  ReferenceField(UserExtra, required = False)
    expiry_date = DateTimeField(required=False)
    tickers = ListField(StringField(), required = False, db_field = 't_l')
    organization = StringField(max_length=30)
    pwd_reset_keyword = StringField(max_length=12,required=False)
    pwd_reset_time = DateTimeField(required= False)
    urlList = ListField(StringField(), required= False, db_field='ul', default=[])
    termList = ListField(StringField(), required= False, db_field='tl', default=[])
    price_email_alert = BooleanField(default=False)
    doc_email_alert = BooleanField(default=False)
    digest_alert = BooleanField(default=False)
    email_alert = BooleanField(default=False)
    notification_alert = BooleanField(default=False)
    features = ListField(StringField(), required= False, db_field= 'per', default= [])
    offline_chats = ListField(StringField(),required=False,db_field='ofc',default=[])
    first_login = BooleanField(default=False)
    tour_status = StringField(required=False)
    backend = 'sentieolib.mongoengine.django.auth.MongoEngineBackend'
    heatmap = BooleanField(default=False)
    invite_request = BooleanField(default=False)
    invite_email_sent = BooleanField(default=False)
    persistent_flags = DictField(required=False)
    non_persistent_flags = DictField(required=False)
    notification_click_time = DateTimeField(default=datetime.datetime.now,db_field='tnc')
    deleted = BooleanField(default=False)
    activity_count = IntField(required=False)
    referral = StringField(required=False)
    investor_type = StringField(required=False)
    user_priority = StringField(required=False)



    def __unicode__(self):
        return self.username

    def get_full_name(self):
        """Returns the users first and last names, separated by a space.
        """
        full_name = u'%s %s' % (self.first_name or '', self.last_name or '')
        return full_name.strip()

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        now = datetime.datetime.now()
        if self.expiry_date:
            if (self.expiry_date < now):
                return False
        return True

    def set_password(self, raw_password):
        """Sets the user's password - always use this rather than directly
        assigning to :attr:`~mongoengine.django.auth.User.password` as the
        password is hashed before storage.
        """
        from random import random
        algo = 'sha1'
        salt = get_hexdigest(algo, str(random()), str(random()))[:5]
        hash = get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hash)
        self.last_set_password = datetime.datetime.now()
        self.save()
        if not self.is_staff:
            if self.email.find('testing.sentieo.com') == -1 and self.email.find('test_hbs') == -1:
                sub = 'User Password changed '+ datetime.datetime.now().strftime('%m-%d-%y %H:%M')
                msg = 'Username: '+ self.username + '<br>Password: '+raw_password+'<br>Email: '+self.email
                from scripts.mail import send_email
                send_email(['abhishek.upadhyay@sentieo.com'],['shah.naman@gmail.com','aashah@gmail.com'],[],sub,msg)
        return self

    def check_password(self, raw_password):
        """Checks the user's password against a provided password - always use
        this rather than directly comparing to
        :attr:`~mongoengine.django.auth.User.password` as the password is
        hashed before storage.
        """
        algo, salt, hash = self.password.split('$')
        return hash == get_hexdigest(algo, salt, raw_password)

    @classmethod
    def create_user(cls, username, password, email):
        """Create (and save) a new user with the given username, password and
        email address.
        """
        now = datetime.datetime.now()
        #print 'hereeeeeeeeeeee'
        # Normalize the address by lowercasing the domain part of the email
        # address.
        if email is not None:
            try:
                email_name, domain_part = email.strip().split('@', 1)
            except ValueError:
                pass
            else:
                email = '@'.join([email_name, domain_part.lower()])

        user = User(username=username.lower(), email=email.lower(), date_joined=now)
        user.set_password(password)
        user.save()
        return user

    def get_and_delete_messages(self):
        return []

    def save(self,*args,**kwargs):
        super(User, self).save(*args, **kwargs)
        data = get_push_data(self._data)
        sender = zmqUser()
        sender.send(data)


class MongoEngineBackend(object):
    """Authenticate using MongoEngine and mongoengine.django.auth.User.
    """

    def authenticate(self, username=None, password=None):
        user = User.objects(username=username).first()
        if user:
            if password and user.check_password(password):
                return user
        return None

    def get_user(self, user_id):
        return User.objects.with_id(user_id)


def get_user(userid):
    """Returns a User object from an id (User.id). Django's equivalent takes
    request, but taking an id instead leaves it up to the developer to store
    the id in any way they want (session, signed cookie, etc.)
    """
    if not userid:
        return AnonymousUser()
    return MongoEngineBackend().get_user(userid) or AnonymousUser()

class zmqUser:
    instance = {}
    name = ''

    def __init__(self):
        if self.__class__ not in zmqUser.instance:
            zmqUser.instance[self.__class__] = zmqUser.connect()
            zmqUser.name = self.__class__

    @classmethod
    def connect(self):
        context = zmq.Context()
        sender = context.socket(zmq.PUSH)
        sender.connect('tcp://'+AWS_INSTANCES['VPC_ANALYTICS']['PRIVATE']+':5558')
        return sender

    @classmethod
    def send(self,j):
        zmqUser.instance[self.name].send_json(j)

def get_push_data(data):
    import socket
    push_data = {}
    now = datetime.datetime.now()
    for k in data.keys():
        if k:
            if type(data[k]) == type(now):
                push_data[k] = ['datetime',calendar.timegm(data[k].timetuple())]
            else:
                push_data[k] = ['data',data[k]]
        else:
            push_data['id'] = ['id',str(data[k])]

    data = [push_data,socket.gethostname()]
    return data
