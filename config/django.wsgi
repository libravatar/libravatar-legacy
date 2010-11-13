import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'libravatar.settings'

import sys
path = '/home/francois/devel/remote/libravatar/'
if path not in sys.path:
    sys.path.append(path)

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
