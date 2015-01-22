__author__ = 'shivnarayan'
import os
import sys
paths = ['/home/ubuntu/projects/','/home/ubuntu/projects/test/']
for path in paths:
    if path not in sys.path:
        sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'test.settings'
from lxml.html import document_fromstring
import re
import urllib
def clean(text):
    text = re.sub('\s*\n\s*', ' ', text)
    text = re.sub('[ \t]{2,}', ' ', text)

    return text.strip()
def html(url):return document_fromstring(urllib.urlopen(url).read())
