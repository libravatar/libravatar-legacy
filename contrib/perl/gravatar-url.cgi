#!/usr/bin/perl
#
# Test for the Libravatar::URL module
#
# You must have symlinks to the libraries in the same directory as this CGI.
#
# e.g.
#  ln -s ~/devel/remote/gravatar_url/lib/Gravatar /var/www/
#  ln -s ~/devel/remote/gravatar_url/lib/Libravatar /var/www/

print "Content-type: text/html\n\n";

use Libravatar::URL;

my $avatar_url = libravatar_url(email => 'fmarier@gmail.com');
my $missing_avatar = libravatar_url(email => 'fmarier+1@gmail.com');

print 'Regular HTTP images:<br>';
print '<img src="' . $avatar_url . '">';
print '<img src="' . $missing_avatar . '">';
print "<br><br>\n";

my $avatar_url = libravatar_url(email => 'fmarier@gmail.com', https => 1);
my $missing_avatar = libravatar_url(email => 'fmarier+1@gmail.com', https => 1);

print 'Regular HTTPS images:<br>';
print '<img src="' . $avatar_url . '">';
print '<img src="' . $missing_avatar . '">';
print "<br><br>\n";

my $avatar_url = libravatar_url(email => 'francois@catalyst.net.nz');
my $missing_avatar = libravatar_url(email => 'francois+1@catalyst.net.nz');

print 'Federated HTTP images:<br>';
print '<img src="' . $avatar_url . '">';
print '<img src="' . $missing_avatar . '">';
print "<br><br>\n";

my $avatar_url = libravatar_url(email => 'francois@catalyst.net.nz', https => 1);
my $missing_avatar = libravatar_url(email => 'francois+1@catalyst.net.nz', https => 1);

print 'Federated HTTPS images:<br>';
print '<img src="' . $avatar_url . '">';
print '<img src="' . $missing_avatar . '">';
print "<br><br>\n";
