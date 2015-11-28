from fabric.api import abort, env, local, parallel, put, roles, run, sudo
from fabric.context_managers import lcd
import re

env.roledefs = {'cdn_only': ['2.cdn.libravatar.org'],
                'seccdn': ['1.cdn.libravatar.org', '5.cdn.libravatar.org'],
                'master': ['0.cdn.libravatar.org'],
                'repo': ['apt.libravatar.org']}

COMMON_PACKAGES = ['libravatar-cdn', 'libravatar-common', 'libravatar-cdn-common', 'libravatar-deployment']
CDNCOMMON_PACKAGES = ['libravatar-slave']
SECCDN_PACKAGES = ['libravatar-seccdn']
MASTER_PACKAGES = ['libravatar', 'libravatar-www', 'libravatar-master']

# Extract current version number from Debian changelog
with open('debian/changelog', 'r') as changelog:
    PACKAGE_VERSION = re.search('\(([0-9]+\.[0-9])\)', changelog.readline()).group(1)


def commit_changelog():
    if local("git status --porcelain", capture=True) != "M debian/changelog":
        abort("You must first update the Debian changelog.")

    local('git commit -a -m "Bump changelog for deployment"', capture=False)


def prepare():
    local('make clean', capture=False)
    commit_changelog()
    print "You must now build the packages in the LXC container: make package"


def sign_repo():
    # from http://blog.mycrot.ch/2011/04/26/creating-your-own-signed-apt-repository-and-debian-packages/
    with lcd('../libravatar-repo/'):
        local('rm -rf db dists pool');
        all_packages = COMMON_PACKAGES + CDNCOMMON_PACKAGES + SECCDN_PACKAGES + MASTER_PACKAGES
        for package_name in all_packages:
            deb = '../%s_%s_all.deb' % (package_name, PACKAGE_VERSION)
            local("/usr/bin/reprepro --ask-passphrase -Vb . includedeb jessie %s" % deb)


@roles('repo')
def upload_packages():
    run('rm -rf /var/www/apt-libravatar/db /var/www/apt-libravatar/dists /var/www/apt-libravatar/pool');
    for directory in ['conf', 'db', 'dists', 'pool']:
        put('../libravatar-repo/%s' % directory, '/var/www/apt-libravatar/')


def update_repo():
    sign_repo()
    upload_packages()


def install_packages(package_names):
    all_debs = ''
    for package_name in package_names:
        all_debs += ' %s' % package_name

    sudo('/usr/bin/apt-get install -y %s' % all_debs, shell=False)


def restart_apache():
    # Restart Apache to make mod_wsgi use the new files
    sudo('/usr/sbin/apache2ctl configtest', shell=False)
    sudo('/usr/sbin/apache2ctl graceful', shell=False)


@parallel
@roles('cdn_only')
def deploy_cdn():
    sudo('/usr/bin/apt-get update', shell=False)
    install_packages(COMMON_PACKAGES + CDNCOMMON_PACKAGES)
    restart_apache()

@parallel
@roles('seccdn')
def deploy_seccdn():
    sudo('/usr/bin/apt-get update', shell=False)
    install_packages(COMMON_PACKAGES + CDNCOMMON_PACKAGES + SECCDN_PACKAGES)
    restart_apache()

@roles('master')
def deploy_master():
    sudo('/usr/bin/apt-get update', shell=False)
    install_packages(COMMON_PACKAGES + MASTER_PACKAGES)
    restart_apache()


def deploy():
    deploy_cdn()
    deploy_seccdn()
    deploy_master()


def stage():
    pass  # TODO: deploy all of the packages to a staging server
