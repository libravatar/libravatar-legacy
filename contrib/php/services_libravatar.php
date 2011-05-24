<?php
/*
 * Test for the Services_Libravatar PEAR package
 *
 * You must have symlinks to the library in the same directory as this file.
 *
 * e.g.
 *  ln -s ~/devel/remote/services_libravatar/Services /var/www/
  */

ini_set('display_errors', true);
ini_set('display_startup_errors', true);
ini_set('error_reporting', E_ALL);
ini_set('html_errors', true);

require_once 'Services/Libravatar.php';

$libravatar = new Services_Libravatar();

$avatar_url = $libravatar->url('fmarier@gmail.com');
$missing_avatar = $libravatar->url('fmarier+1@gmail.com');

print 'Regular HTTP images:<br>';
print '<img src="' . $avatar_url . '">';
print '<img src="' . $missing_avatar . '">';
print "<br><br>\n";

$avatar_url = $libravatar->url('fmarier@gmail.com', array('https' => true));
$missing_avatar = $libravatar->url('fmarier+1@gmail.com', array('https' => true));

print 'Regular HTTPS images:<br>';
print '<img src="' . $avatar_url . '">';
print '<img src="' . $missing_avatar . '">';
print "<br><br>\n";

$avatar_url = $libravatar->url('francois@catalyst.net.nz');
$missing_avatar = $libravatar->url('francois+1@catalyst.net.nz');

print 'Federated HTTP images:<br>';
print '<img src="' . $avatar_url . '">';
print '<img src="' . $missing_avatar . '">';
print "<br><br>\n";

$avatar_url = $libravatar->url('francois@catalyst.net.nz', array('https' => true));
$missing_avatar = $libravatar->url('francois+1@catalyst.net.nz', array('https' => true));

print 'Federated HTTPS images:<br>';
print '<img src="' . $avatar_url . '">';
print '<img src="' . $missing_avatar . '">';
print "<br><br>\n";

$avatar_url = $libravatar->url('https://launchpad.net/~fmarier');
$missing_avatar = $libravatar->url('http://launchpad.net/~notfmarier');

print 'Regular HTTP images (OpenID):<br>';
print '<img src="' . $avatar_url . '">';
print '<img src="' . $missing_avatar . '">';
print "<br><br>\n";
