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

import base64
import gzip
import json
import os
import sys
from xml.sax import saxutils

import settings # pylint: disable=W0403
from utils import create_logger, is_hex # pylint: disable=W0403

logger = create_logger('exportaccount')

SCHEMA_ROOT = 'http://www.libravatar.org/schemas/export/0.1'
SCHEMA_XSD = '%s/export.xsd' % SCHEMA_ROOT

def xml_header():
    return '''<?xml version="1.0" encoding="UTF-8"?>
<user xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="%s %s"
      xmlns="%s">\n''' % (SCHEMA_ROOT, SCHEMA_XSD, SCHEMA_ROOT)

def xml_footer():
    return '</user>\n'

def xml_account(username):
    escaped_username = saxutils.quoteattr(username)
    escaped_site_url = saxutils.quoteattr(settings.SITE_URL)
    return '  <account username=%s site=%s/>\n' % (escaped_username, escaped_site_url)

def xml_list(list_type, list_elements):
    s = '  <%ss>\n' % list_type
    for element in list_elements:
        s += '    <%s>%s</%s>\n' % (list_type, saxutils.escape(element), list_type)
    s += '  </%ss>\n' % list_type
    return s

def xml_photos(photos):
    s = '  <photos>\n'
    for photo in photos:
        (photo_filename, photo_format) = photo
        encoded_photo = encode_photo(photo_filename, photo_format)
        if encoded_photo:
            s += '''    <photo encoding="base64" format=%s>
%s
    </photo>\n''' % (saxutils.quoteattr(photo_format), encoded_photo)
    s += '  </photos>\n'
    return s

def encode_photo(photo_filename, photo_format):
    filename = settings.USER_FILES_ROOT + photo_filename + '.' + photo_format
    if not os.path.isfile(filename):
        logger.warning('Photo not found: %s' % filename)
        return None

    photo_content = None
    with open(filename) as photo:
        photo_content = photo.read()

    if not photo_content:
        logger.warning('Could not read photo: %s' % filename)
        return None

    return base64.b64encode(photo_content)

def main(argv=None):
    if argv is None:
        argv = sys.argv

    gearman_workload = sys.stdin.read()
    params = json.loads(gearman_workload)

    do_delete = params['do_delete']
    file_hash = params['file_hash']
    username = params['username']
    emails = params['emails']
    openids = params['openids']
    photos = params['photos']

    # Validate inputs
    if file_hash and not is_hex(file_hash):
        logger.error('file_hash is not a hexadecimal value')
        return 1
    for photo in photos:
        (photo_filename, photo_format) = photo
        if not is_hex(photo_filename):
            logger.error("photo_filename '%s' is not a hexadecimal value" % photo_filename)
            return 1
        if photo_format != 'jpg' and photo_format != 'png':
            logger.error("photo_format '%s' is not recognized" % photo_format)
            return 1

    dest_filename = settings.EXPORT_FILES_ROOT + file_hash + '.xml.gz'
    destination = gzip.open(dest_filename, 'w')
    destination.write(xml_header())
    destination.write(xml_account(username))
    destination.write(xml_list('email', emails))
    destination.write(xml_list('openid', openids))
    destination.write(xml_photos(photos))
    destination.write(xml_footer())
    destination.close()

    if do_delete:
        # TODO: kick off a photo deletion worker
        pass

    return 0

if __name__ == "__main__":
    sys.exit(main())
