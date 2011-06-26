#!/usr/bin/ruby
#
# Test for the libravatar gem
#
# You must have a symlink to the library in the same directory as this CGI.
#
# e.g.
#  ln -s ~/devel/remote/libravatar-gem/lib/libravatar.rb /var/www/

puts "Content-Type: text/html"
puts

require 'libravatar'

avatar_url = Libravatar.new(:email => "fmarier@gmail.com")
missing_avatar = Libravatar.new(:email => "fmarier+1@gmail.com")

print 'Regular HTTP images:<br>'
print '<img src="', avatar_url, '">'
print '<img src="', missing_avatar, '">'
print "<br><br>\n"

avatar_url = Libravatar.new(:email => "fmarier@gmail.com", :https => true)
missing_avatar = Libravatar.new(:email => "fmarier+1@gmail.com", :https => true)

print 'Regular HTTPS images:<br>'
print '<img src="', avatar_url, '">'
print '<img src="', missing_avatar, '">'
print "<br><br>\n"

avatar_url = Libravatar.new(:email => "francois@catalyst.net.nz")
missing_avatar = Libravatar.new(:email => "francois+1@catalyst.net.nz")

print 'Federated HTTP images:<br>'
print '<img src="', avatar_url, '">'
print '<img src="', missing_avatar, '">'
print "<br><br>\n"

avatar_url = Libravatar.new(:email => "francois@catalyst.net.nz", :https => true)
missing_avatar = Libravatar.new(:email => "francois+1@catalyst.net.nz", :https => true)

print 'Federated HTTPS images:<br>'
print '<img src="', avatar_url, '">'
print '<img src="', missing_avatar, '">'
print "<br><br>\n"

avatar_url = Libravatar.new(:openid => 'https://launchpad.net/~fmarier')
missing_avatar = Libravatar.new(:openid => 'https://launchpad.net/~notfmarier')

print 'Regular HTTP images (OpenID):<br>'
print '<img src="', avatar_url, '">'
print '<img src="', missing_avatar, '">'
print "<br><br>\n"
