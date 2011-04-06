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
import sys

import settings # pylint: disable=W0403
from utils import create_logger, is_hex # pylint: disable=W0403

logger = create_logger('exportaccount')

def main(argv=None):
    if argv is None:
        argv = sys.argv

    gearman_workload = sys.stdin.read()
    params = json.loads(gearman_workload)

    do_delete = params['do_delete']
    file_hash = params['file_hash']

    # Validate inputs
    if file_hash and not is_hex(file_hash):
        logger.error('file_hash is not a hexadecimal value')
        return 1

    dest_filename = settings.EXPORT_FILES_ROOT + file_hash + '.xml'
    destination = open(dest_filename, 'w')
    destination.write('<?xml version="1.0"?>\n<libravatar-user>TODO</libravatar-user>')
    destination.close()

    if do_delete:
        # TODO: kick off a photo deletion worker
        pass

    return 0

if __name__ == "__main__":
    sys.exit(main())
