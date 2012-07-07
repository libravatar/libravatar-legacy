# Branding/homepage:

* make a collage of the user photos in the shape of libravatar logo (the ones licensed under Creative Commons)
* improve basic layout (using http://960.gs/ maybe?)

# Federation

* create a test [mugshots.debian.net](http://liw.iki.fi/liw/log/2006-11.html#20061127b) server with db.people.org auth as [suggested by Lars](http://www.mail-archive.com/debian-project@lists.debian.org/msg00572.html))

# Gearman jobs

* make gearman jobs persist (inside a Redis DB?) but not inside the main Pg DB

# Sysadmin stuff

* create a staging server to test deployments
* create a public package repository to upload libravatar packages
* use rsyslog to copy logs to another machine
* use Puppet or [Salt](http://saltstack.org) for all server config
* monitor server with Nagios
* monitor gearman queues (http://labs.consol.de/nagios/mod-gearman/)
* use [mod_spdy](https://code.google.com/p/mod-spdy/) on seccdn.libravatar.org
