from django.contrib.sessions.backends.base import SessionBase, CreateError
from django.core.exceptions import SuspiciousOperation
from django.utils.encoding import force_unicode

from sentieolib.mongoengine.document import Document
from sentieolib.mongoengine import fields
from sentieolib.mongoengine.queryset import OperationError

from datetime import datetime
import json
import httpagentparser


class MongoSession(Document):
    session_key = fields.StringField(primary_key=True, max_length=40)
    session_data = fields.StringField()
    expire_date = fields.DateTimeField()
    user_id     = fields.StringField()
    user_agent  = fields.StringField()
    device_id   = fields.StringField()
    
    meta = {'collection': 'django_session', 'allow_inheritance': False}

    def embed(self):
        user_id = self.user_id if self.user_id else ''
        device_id = self.device_id if self.device_id else ''
        user_agent = ''
        if self.user_agent:
            value = json.loads(self.user_agent).get('ua')
            if value:
                dict = httpagentparser.detect(value)
                try:
                    browser = dict['browser']['name'] + ' ' +dict.get('browser',{}).get('version','')
                    os = dict['os']['name']+'  '+dict.get('os',{}).get('version','')
                    user_agent = 'Browser : '+browser+', OS : '+os

                except :
                    # return value
                    user_agent = ''
            else:
                user_agent = ''
        else:
            user_agent = ''

        return {'session_key':self.session_key,
                'user_id':user_id,
                'device_id':device_id,
                'user_agent':user_agent}


class SessionStore(SessionBase):
    """A MongoEngine-based session store for Django.
    """

    def load(self):
        try:
            s = MongoSession.objects(session_key=self.session_key,
                                     expire_date__gt=datetime.now())[0]
            return self.decode(force_unicode(s.session_data))
        except (IndexError, SuspiciousOperation):
            self.create()
            return {}

    def exists(self, session_key):
        return bool(MongoSession.objects(session_key=session_key).first())

    def create(self):
        while True:
            self.session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                continue
            self.modified = True
            self._session_cache = {}
            return

    def save(self, must_create=False):
        s = MongoSession(session_key=self.session_key)
        data =  self._get_session(no_load=must_create)
        s.session_data = self.encode(data)
        s.expire_date = self.get_expiry_date()
        s.user_id = data.get('_user_id','')
        s.device_id = data.get('_dev_id','')
        s.user_agent = data.get('_user_agent','')
        try:
            s.save(force_insert=must_create, safe=True)
        except OperationError:
            if must_create:
                raise CreateError
            raise

    def delete(self, session_key=None):
        if session_key is None:
            if self.session_key is None:
                return
            session_key = self.session_key
        MongoSession.objects(session_key=session_key).delete()

    def set_user_id(self,userid):
        try:
            s = MongoSession.objects(session_key=self.session_key,
                                     expire_date__gt=datetime.now())[0]

            s.user_id = userid

            s.save()
            return 'uid Success '+userid+' '+self.session_key+' '
        except (IndexError, SuspiciousOperation):
            import traceback
            return 'set_user_id \n\n'+traceback.format_exc()

    def get_user_id(self):
        try:
            s = MongoSession.objects(session_key=self.session_key,
                                     expire_date__gt=datetime.now())[0]

            return s.user_id
        except (IndexError, SuspiciousOperation):
            return ''

    def set_user_agent(self,useragent):
        try:
            s = MongoSession.objects(session_key=self.session_key,
                                     expire_date__gt=datetime.now())[0]

            if type(useragent) == type({}):
                useragent = json.dumps(useragent)
            s.user_agent = useragent

            s.save()
            return 'ua Success '+useragent
        except (IndexError, SuspiciousOperation):
            import traceback
            return 'set_user_agent \n\n'+traceback.format_exc()

    def get_user_agent(self):
        try:
            s = MongoSession.objects(session_key=self.session_key,
                                     expire_date__gt=datetime.now())[0]

            if s.user_agent:
                return json.loads(s.user_agent)
            else:
                return {}
        except (IndexError, SuspiciousOperation):
            return {}

    def set_device_id(self,deviceid):
        try:
            s = MongoSession.objects(session_key=self.session_key,
                                     expire_date__gt=datetime.now())[0]

            s.device_id = deviceid
            s.save()
            return 'di Success '+deviceid
        except (IndexError, SuspiciousOperation):
            import traceback
            return 'set_di \n\n'+traceback.format_exc()

    def get_device_id(self):
        try:
            s = MongoSession.objects(session_key=self.session_key,
                                     expire_date__gt=datetime.now())[0]

            return s.device
        except (IndexError, SuspiciousOperation):
            pass


    def get_session_id(self):
        return self.session_key
    # def __contains__(self, key):
    #     return key in self._session
    #
    # def __getitem__(self, key):
    #     return self._session[key]
    #
    # def __setitem__(self, key, value):
    #     self._session[key] = value
    #     self.modified = True
    #
    # def __delitem__(self, key):
    #     del self._session[key]
    #     self.modified = True








