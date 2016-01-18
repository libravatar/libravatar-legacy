#!/usr/bin/python
# Copyright (C) 2011, 2013, 2016  Francois Marier <francois@libravatar.org>
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

import gearman
import json
import os
import shutil
import sys

# pylint: disable=W0403
import settings
from utils import create_logger, delete_if_exists, is_hex, is_hash_pair

os.umask(022)
logger = create_logger('ready2user')


def main(argv=None):
    if argv is None:
        argv = sys.argv

    gearman_workload = sys.stdin.read()
    params = json.loads(gearman_workload)

    file_hash = params['file_hash']
    file_format = params['format']
    links = params['links']

    # Validate inputs
    if not is_hex(file_hash):
        logger.error('file_hash is not a hexadecimal value')
        return 1
    if file_format != 'jpg' and file_format != 'png' and file_format != 'gif':
        logger.error('file_format is not recognized')
        return 1
    if not isinstance(links, list):
        logger.error('links is not a list')
        return 1
    for l in links:
        if not is_hash_pair(l):
            logger.error('links is not a list of hash pairs')
            return 1

    filename = "%s.%s" % (file_hash, file_format)
    source = settings.READY_FILES_ROOT + filename
    dest = settings.USER_FILES_ROOT + filename

    # Sanity checks
    if os.path.isfile(dest):
        logger.warning('Destination already exists')
        return 0

    if not os.path.isfile(source):
        logger.error('Source file not found')
        return 1

    # Remove from /ready and move to /user
    try:
        shutil.move(source, dest)
    except:
        logger.error('Cannot move file')
        return 2

    # All done, we can delete the original file as uploaded by the user
    uploaded_file = settings.UPLOADED_FILES_ROOT + filename
    delete_if_exists(uploaded_file)

    # Finally, create any links to email hashes that were requested
    gm_client = gearman.GearmanClient(settings.GEARMAN_SERVERS)
    for hashes in links:
        params = {'photo_hash': file_hash, 'photo_format': file_format,
                  'md5_hash': hashes[0], 'sha256_hash': hashes[1]}
        gm_client.submit_job('changephoto', json.dumps(params),
                             background=True, wait_until_complete=False)

    return 0

if __name__ == "__main__":
    sys.exit(main())
