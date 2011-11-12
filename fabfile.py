from fabric.api import abort, env, local, put, roles
import re

env.roledefs = {'slave': ['1.cdn.libravatar.org', '2.cdn.libravatar.org', '3.cdn.libravatar.org'],
                'master': ['0.cdn.libravatar.org']}

COMMON_PACKAGES = ['libravatar-cdn', 'libravatar-common', 'libravatar-cdn-common']
SLAVE_PACKAGES = ['libravatar-seccdn', 'libravatar-slave']
MASTER_PACKAGES = ['libravatar', 'libravatar-www', 'libravatar-master']

# Extract current version number from Debian changelog
with open('debian/changelog', 'r') as changelog:
    PACKAGE_VERSION = re.search('\(([0-9]+\.[0-9])\)', changelog.readline()).group(1)


def commit_changelog():
    if local("bzr status --short", capture=True) != 'M  debian/changelog':
        abort("You must first update the Debian changelog.")

    local('bzr commit -m "Bump changelog for deployment"', capture=False)


def build_package():
    local('make package', capture=False)


def prepare():
    local('make clean', capture=False)
    commit_changelog()
    build_package()


def copy_common_packages():
    for package_name in COMMON_PACKAGES:
        put('../%s_%s_all.deb' % (package_name, PACKAGE_VERSION), '~')
    # TODO: install all packages using sudo
    # TODO: deal with etckeeper (check that the git branch is clean, then commit automatically)
    # TODO: restart apache


@roles('slave')
def deploy_slave():
    copy_common_packages()
    # TODO: copy slave-related packages onto the slave


@roles('master')
def deploy_master():
    copy_common_packages()
    # TODO: copy master-related packages on the master


def deploy():
    deploy_slave()
    deploy_master()


def stage():
    pass # TODO: deploy all of the packages to a staging server
