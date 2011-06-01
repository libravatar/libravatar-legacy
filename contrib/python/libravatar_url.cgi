#!/usr/bin/python
#
# Test for the pyLibravatar module
#
# You must have a symlink to the library in the same directory as this CGI.
#
# e.g.
#  ln -s ~/devel/remote/pylibravatar/libravatar.py /var/www/

from libravatar import libravatar_url

print 'Content-type: text/html\n\n'

avatar_url = libravatar_url(email = 'fmarier@gmail.com')
missing_avatar = libravatar_url(email = 'fmarier+1@gmail.com')

print 'Regular HTTP images:<br>'
print '<img src="' + avatar_url + '">'
print '<img src="' + missing_avatar + '">'
print "<br><br>\n"

avatar_url = libravatar_url(email = 'fmarier@gmail.com', https = 1)
missing_avatar = libravatar_url(email = 'fmarier+1@gmail.com', https = 1)

print 'Regular HTTPS images:<br>'
print '<img src="' + avatar_url + '">'
print '<img src="' + missing_avatar + '">'
print "<br><br>\n"

avatar_url = libravatar_url(email = 'francois@catalyst.net.nz')
missing_avatar = libravatar_url(email = 'francois+1@catalyst.net.nz')

print 'Federated HTTP images:<br>'
print '<img src="' + avatar_url + '">'
print '<img src="' + missing_avatar + '">'
print "<br><br>\n"

avatar_url = libravatar_url(email = 'francois@catalyst.net.nz', https = 1)
missing_avatar = libravatar_url(email = 'francois+1@catalyst.net.nz', https = 1)

print 'Federated HTTPS images:<br>'
print '<img src="' + avatar_url + '">'
print '<img src="' + missing_avatar + '">'
print "<br><br>\n"

avatar_url = libravatar_url(openid = 'https://launchpad.net/~fmarier')
missing_avatar = libravatar_url(openid = 'https://launchpad.net/~notfmarier')

print 'Regular HTTP images (OpenID):<br>'
print '<img src="' + avatar_url + '">'
print '<img src="' + missing_avatar + '">'
print "<br><br>\n"

