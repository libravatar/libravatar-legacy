#!/usr/bin/python
# Copyright (C) 2011  Francois Marier <francois@libravatar.org>
#
# This file is part of Libravatar
# 
# Libravatar is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Libravatar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with Libravatar.  If not, see <http://www.gnu.org/licenses/>.

import json
from os import link, path
import sys

import settings # pylint: disable=W0403
from resizeavatar import resize_image # pylint: disable=W0403
from utils import create_logger, delete_if_exists, is_hex # pylint: disable=W0403

logger = create_logger('changephoto')

def link_image(source_filename, destination_hash, size=None):
    if size:
        destination_filename = settings.AVATAR_ROOT + '%s/%s' % (size, destination_hash)
    else:
        destination_filename = settings.AVATAR_ROOT + destination_hash

    try:
        link(source_filename, destination_filename)
    except OSError:
        logger.error("Unable to link '%s' to %s" % (source_filename, destination_filename))

def create_links(source_filename, md5_hash, sha256_hash):
    if not path.isfile(source_filename):
        logger.warning("the cropped photo '%s' does not exist" % source_filename)
        return 0

    if md5_hash:
        link_image(source_filename, md5_hash)
    link_image(source_filename, sha256_hash)

    # Generate resized images for common sizes
    for size in settings.AVATAR_PREGENERATED_SIZES:
        resized_filename = resize_image(sha256_hash, size)
        if md5_hash:
            link_image(resized_filename, md5_hash, size)

    return 0

def main(argv=None):
    if argv is None:
        argv = sys.argv

    gearman_workload = sys.stdin.read()
    params = json.loads(gearman_workload)

    photo_hash = params['photo_hash']
    photo_format = params['photo_format']
    md5_hash = params['md5_hash']
    sha256_hash = params['sha256_hash']

    # Validate inputs
    if photo_hash and not is_hex(photo_hash):
        logger.error('photo_hash is not a hexadecimal value')
        return 1
    if photo_format and photo_format != 'jpg' and photo_format != 'png':
        logger.error('photo_format is not recognized')
        return 1
    if md5_hash and not is_hex(md5_hash):
        logger.error('md5_hash is not a hexadecimal value')
        return 1
    if not is_hex(sha256_hash): # mandatory
        logger.error('sha256_hash is not a hexadecimal value')
        return 1

    # Remove old image
    if md5_hash:
        delete_if_exists(settings.AVATAR_ROOT + md5_hash)
    delete_if_exists(settings.AVATAR_ROOT + sha256_hash)

    # Delete all resized images
    for size in xrange(settings.AVATAR_MIN_SIZE, settings.AVATAR_MAX_SIZE):
        size_dir = settings.AVATAR_ROOT + '%s/' % size

        if md5_hash:
            delete_if_exists(size_dir + md5_hash)
        delete_if_exists(size_dir + sha256_hash)

    if not photo_hash:
        return 0

    source_filename = settings.USER_FILES_ROOT + photo_hash + '.' + photo_format
    return create_links(source_filename, md5_hash, sha256_hash)

if __name__ == "__main__":
    sys.exit(main())
