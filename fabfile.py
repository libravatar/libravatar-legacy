from fabric.api import abort, env, local, put, roles, run, sudo
import re

try:
    # This will fail on Squeeze's version of fabric
    from fabric.api import parallel
except ImportError:
    # Define a stub decorator that doesn't do anything
    def parallel(function):
        return function

try:
    # This will fail on Squeeze's version of fabric
    from fabric.context_managers import lcd
except ImportError:
    # Define a stub context manager that doesn't do anything
    def lcd():
        return None

env.roledefs = {'slave': ['1.cdn.libravatar.org', '2.cdn.libravatar.org', '3.cdn.libravatar.org'],
                'master': ['0.cdn.libravatar.org'],
                'repo': ['apt.libravatar.org']}

COMMON_PACKAGES = ['libravatar-cdn', 'libravatar-common', 'libravatar-cdn-common', 'libravatar-deployment']
SLAVE_PACKAGES = ['libravatar-seccdn', 'libravatar-slave']
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
    local('make package', capture=False)


def sign_repo():
    # from http://blog.mycrot.ch/2011/04/26/creating-your-own-signed-apt-repository-and-debian-packages/
    with lcd('../libravatar-repo/'):
        local('rm -rf db dists pool');
        all_packages = COMMON_PACKAGES + SLAVE_PACKAGES + MASTER_PACKAGES
        for package_name in all_packages:
            deb = '../%s_%s_all.deb' % (package_name, PACKAGE_VERSION)
            local("/usr/bin/reprepro --ask-passphrase -Vb . includedeb squeeze %s" % deb)


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
@roles('slave')
def deploy_slave():
    sudo('/usr/bin/apt-get update', shell=False)
    install_packages(COMMON_PACKAGES + SLAVE_PACKAGES)
    restart_apache()


@roles('master')
def deploy_master():
    sudo('/usr/bin/apt-get update', shell=False)
    install_packages(COMMON_PACKAGES + MASTER_PACKAGES)
    restart_apache()


def deploy():
    deploy_slave()
    deploy_master()


def stage():
    pass  # TODO: deploy all of the packages to a staging server
