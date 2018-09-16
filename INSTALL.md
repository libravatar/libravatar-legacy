*Note: these installation instructions are for the main libravatar.org service, not for mirrors. If you're interested in running a mirror, see <https://wiki.libravatar.org/run_a_mirror/> instead.*

# External dependencies

* Python 2.7
* Django 1.8
* Apache 2 with:
 * mod\_alias
 * mod\_expires
 * mod\_headers
 * mod\_rewrite
* [Python DNS 2.3.6](http://pydns.sourceforge.net/)
* jQuery 1.7.2
* [Python Imaging Library](http://www.pythonware.com/library/)
* [YUI Compressor](http://developer.yahoo.com/yui/compressor/), for minifying CSS/JS files
* [Gearman](http://www.gearman.org)
* [Python bcrypt](https://pypi.python.org/pypi/bcrypt)
* [Python Gearman](https://pypi.python.org/pypi/gearman)
* [Python OpenID](https://github.com/openid/python-openid)
* [OpenID Integration for django.contrib.auth](https://launchpad.net/django-openid-auth)
* [Requests](http://python-requests.org/)
* Python LDAP library (if using optional LDAP authenticaion)
* PNG crush
* AdvanceCOMP
* GIFsicle

On Debian unstable or jessie:

    apt-get install python-django python-dns libjs-jquery python-imaging libapache2-mod-wsgi python-psycopg2 yui-compressor gearman-job-server gearman-tools python-gearman jpegoptim optipng python-openid python-django-auth-openid python-requests ca-certificates pngcrush advancecomp gifsicle python-bcrypt
  
    apt-get install python-ldap


# Create your database

Create a database user:

    sudo -u postgres createuser djangouser

Create a database:

    sudo -u postgres createdb -O djangouser libravatar

Create the required tables:

    cd /usr/share/libravatar
    python manage.py migrate

# Apache Configuration

Start by adding this to your /etc/hosts:

    127.0.0.1 www.libravatar.org cdn.libravatar.org seccdn.libravatar.org

Enable mod\_alias, mod\_expires, mod\_headers, mod\_rewrite, mod\_ssl and mod\_wsgi:

    a2enmod alias
    a2enmod expires
    a2enmod headers
    a2enmod rewrite
    a2enmod ssl
    a2enmod wsgi

and put the following in `/etc/apache2/conf-available/tls.conf`:

    SSLProtocol             all -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite          ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256
    SSLHonorCipherOrder     on
    SSLCompression          off
    
    SSLUseStapling          on
    SSLStaplingResponderTimeout 5
    SSLStaplingReturnResponderErrors off
    SSLStaplingCache shmcb:/var/run/ocsp(128000)

before enabling it:

    a2enconf tls

Create an uploaded/ directory that is writable by the www-data user:

    mkdir /var/lib/libravatar/uploaded
    sudo chgrp www-data /var/lib/libravatar/uploaded
    sudo chmod g+w /var/lib/libravatar/uploaded

as well as ready/ and user/ directories which are not writable by www-data:

    mkdir /var/lib/libravatar/ready
    mkdir /var/lib/libravatar/user

Similarly, avatar/ and export directories that are only writable by root:

    mkdir /var/lib/libravatar/avatar
    mkdir /var/lib/libravatar/export

Then copy config/*.conf to /etc/apache2/sites-enabled/, adjust the
path to the cdn-common include file and restart Apache using:

    apache2ctl configtest
    apache2ctl restart


# Gearman jobs

A few Gearman jobs must be running to fully take care of photo management:

* cropresize: must run under a user that has read access to /uploaded and
              write access to /ready
* ready2user: must run under a user with read access to /ready and write
              access to /uploaded and /user
* changephoto: must run as root
* deletephoto: must run as root
* resizeavatar: must run as root
* exportaccount: must run as root

There are python scripts under libravatar/ for all of these functions and
workers can be setup like this:

    gearman -w -f FUNCTION_NAME libravatar/FUNCTION_NAME.py


# Cron job

You should have a daily cron job which does the following:

* delete old sessions and exports
* delete old uploaded (i.e. non-cropped) files

Have a look in debian/libravatar-www.cron.daily for an example.


# Authenticating with an external LDAP server:

Download and install the [Django LDAP authentication backend](http://packages.python.org/django-auth-ldap/):

    apt-get install python-django-auth-ldap

Then uncomment the LDAP backend line in AUTHENTICATION\_BACKENDS in your
settings.py and set your AUTH\_LDAP\_SERVER\_URI and AUTH\_LDAP\_USER\_DN\_TEMPLATE
settings to something appropriate. More complex setups are also well documented
in the [package documentation](https://django-auth-ldap.readthedocs.io/en/latest/).
