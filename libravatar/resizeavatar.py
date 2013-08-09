#!/usr/bin/python
# Copyright (C) 2011, 2013  Francois Marier <francois@libravatar.org>
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

import Image
import json
import os
import sys

# pylint: disable=W0403
import settings
from utils import create_logger, is_hex

os.umask(022)
logger = create_logger('resizeavatar')


def resize_image(email_hash, size):
    original_filename = settings.AVATAR_ROOT + email_hash

    output_dir = settings.AVATAR_ROOT + '/%s' % size
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    resized_filename = '%s/%s' % (output_dir, email_hash)

    # Save resized image to disk
    original_img = Image.open(original_filename)
    resized_img = original_img.resize((size, size), Image.ANTIALIAS)
    resized_img.save(resized_filename, original_img.format, quality=settings.JPEG_QUALITY)

    return resized_filename


def main(argv=None):
    if argv is None:
        argv = sys.argv

    gearman_workload = sys.stdin.read()
    params = json.loads(gearman_workload)

    email_hash = params['email_hash']
    size = int(params['size'])

    # Validate inputs
    if not is_hex(email_hash):
        logger.error('email_hash is not a hexadecimal value')
        return 1

    resize_image(email_hash, size)

    # TODO: use find -inum on the original inode to find other hashes
    # then hardlink the resized image to the other hashes

    return 0

if __name__ == "__main__":
    sys.exit(main())
