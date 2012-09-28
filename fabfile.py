from fabric.api import abort, env, local, put, roles, run, sudo
import re

try:
    # This will fail on Squeeze's version of fabric
    from fabric.api import parallel
except ImportError:
    # Define a stub decorator that doesn't do anything
    def parallel(function):
        return function

env.roledefs = {'slave': ['1.cdn.libravatar.org', '2.cdn.libravatar.org', '3.cdn.libravatar.org'],
                'master': ['0.cdn.libravatar.org']}

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


def copy_and_install_packages(package_names):
    all_debs = ''
    for package_name in package_names:
        deb = '%s_%s_all.deb' % (package_name, PACKAGE_VERSION)
        all_debs += ' /home/%s/debs/%s' % (env.user, deb)
        put('../%s' % deb, 'debs/')

    sudo('/usr/bin/dpkg -i%s' % all_debs, shell=False)


def restart_apache():
    # Restart Apache to make mod_wsgi use the new files
    sudo('/usr/sbin/apache2ctl configtest', shell=False)
    sudo('/usr/sbin/apache2ctl graceful', shell=False)


def commit_etc_changes():
    # TODO: deal with etckeeper (check that the git branch is clean, then commit automatically)
    pass


@parallel
@roles('slave')
def deploy_slave():
    run('mkdir -p debs')  # ensure the target directory exists
    copy_and_install_packages(COMMON_PACKAGES)
    copy_and_install_packages(SLAVE_PACKAGES)
    restart_apache()
    commit_etc_changes()


@roles('master')
def deploy_master():
    run('mkdir -p debs')  # ensure the target directory exists
    copy_and_install_packages(COMMON_PACKAGES)
    copy_and_install_packages(MASTER_PACKAGES)
    restart_apache()
    commit_etc_changes()


def deploy():
    deploy_slave()
    deploy_master()


def stage():
    pass  # TODO: deploy all of the packages to a staging server
