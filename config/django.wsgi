import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'libravatar.settings'

import sys
path = '/usr/share/libravatar/'
if path not in sys.path:
    sys.path.append(path)

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
