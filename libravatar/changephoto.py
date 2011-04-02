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

def main(argv=None):
    if argv is None:
        argv = sys.argv

    gearman_workload = sys.stdin.read()
    params = json.loads(gearman_workload)

    photo_hash = params['photo_hash']
    photo_format = params['photo_format']
    md5_hash = params['md5_hash']
    sha1_hash = params['sha1_hash']
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
    if sha1_hash and not is_hex(sha1_hash):
        logger.error('sha1_hash is not a hexadecimal value')
        return 1
    if sha256_hash and not is_hex(sha256_hash):
        logger.error('sha256_hash is not a hexadecimal value')
        return 1

    # TODO: use git-like hashed directories to avoid too many files in one directory
    md5_filename = settings.AVATAR_ROOT + md5_hash
    sha1_filename = settings.AVATAR_ROOT + sha1_hash
    sha256_filename = settings.AVATAR_ROOT + sha256_hash

    # Remove old image
    delete_if_exists(md5_filename)
    delete_if_exists(sha1_filename)
    delete_if_exists(sha256_filename)

    # Delete all resized images
    for size in xrange(settings.AVATAR_MIN_SIZE, settings.AVATAR_MAX_SIZE):
        size_dir = settings.AVATAR_ROOT + '/%s/' % size

        delete_if_exists(size_dir + md5_hash)
        delete_if_exists(size_dir + sha1_hash)
        delete_if_exists(size_dir + sha256_hash)

    if not photo_hash:
        return 0

    source_filename = settings.USER_FILES_ROOT + photo_hash + '.' + photo_format
    if not path.isfile(source_filename):
        logger.warn("the cropped photo '%s' does not exist" % source_filename)
        return 0

    link(source_filename, md5_filename)
    link(source_filename, sha1_filename)
    link(source_filename, sha256_filename)

    # Generate resized images for common sizes
    for size in settings.AVATAR_PREGENERATED_SIZES:
        resized_filename = resize_image(md5_hash, size)

        output_dir = settings.AVATAR_ROOT + '/%s/' % size
        link(resized_filename, output_dir + sha1_hash)
        link(resized_filename, output_dir + sha256_hash)

    return 0

if __name__ == "__main__":
    sys.exit(main())
