import os, stat, sys

INSTALL_PATH = '/usr/share/libravatar/'
CONFIG_FILE = INSTALL_PATH + 'libravatar/settings.py'

# Make sure the config file is protected against unauthorized changes
if (os.stat(CONFIG_FILE).st_uid != 0) or (os.stat(CONFIG_FILE).st_gid != 0):
    print "settings.py file must be owned by root:root"
    sys.exit(1)
group_writable = bool(os.stat(CONFIG_FILE).st_mode & stat.S_IWGRP)
other_writable = bool(os.stat(CONFIG_FILE).st_mode & stat.S_IWOTH)
if group_writable or other_writable:
    print "settings.py file must only be writable by its owner"
    sys.exit(2)

os.environ['DJANGO_SETTINGS_MODULE'] = 'libravatar.settings'

if INSTALL_PATH not in sys.path:
    sys.path.append(INSTALL_PATH)

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
