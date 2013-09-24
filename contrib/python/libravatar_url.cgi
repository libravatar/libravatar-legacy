#!/usr/bin/python
#
# Test for the pyLibravatar module
#
# You must have a symlink to the library in the same directory as this CGI.
#
# e.g.
#  ln -s ~/devel/remote/pylibravatar/libravatar.py /var/www/

from __future__ import print_function

import os, sys
cmd_folder = os.path.dirname(os.path.abspath(__file__))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

from libravatar import libravatar_url

print('Content-type: text/html\n\n')
print("<h1>pyLibravatar</h1>")

avatar_url = libravatar_url(email = 'fmarier@gmail.com')
missing_avatar = libravatar_url(email = 'fmarier+1@gmail.com')

print('Regular HTTP images:<br>')
print('<img src="' + avatar_url + '">')
print('<img src="' + missing_avatar + '">')
print("<br><br>\n")

avatar_url = libravatar_url(email = 'fmarier@gmail.com', https = 1)
missing_avatar = libravatar_url(email = 'fmarier+1@gmail.com', https = 1)

print('Regular HTTPS images:<br>')
print('<img src="' + avatar_url + '">')
print('<img src="' + missing_avatar + '">')
print("<br><br>\n")

avatar_url = libravatar_url(email = 'francois@fmarier.org')
missing_avatar = libravatar_url(email = 'francois+1@fmarier.org')

print('Federated HTTP images:<br>')
print('<img src="' + avatar_url + '">')
print('<img src="' + missing_avatar + '">')
print("<br><br>\n")

avatar_url = libravatar_url(email = 'francois@fmarier.org', https = 1)
missing_avatar = libravatar_url(email = 'francois+1@fmarier.org', https = 1)

print('Federated HTTPS images:<br>')
print('<img src="' + avatar_url + '">')
print('<img src="' + missing_avatar + '">')
print("<br><br>\n")

avatar_url = libravatar_url(openid = 'https://openid.fmarier.org/')
missing_avatar = libravatar_url(openid = 'https://openid.fmarier.org/invalid')

print('Regular HTTP images (OpenID):<br>')
print('<img src="' + avatar_url + '">')
print('<img src="' + missing_avatar + '">')
print("<br><br>\n")

