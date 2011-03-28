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

from gearman import libgearman
import Image
import json
import os
import sys

import settings # pylint: disable=W0403
from utils import delete_if_exists, is_hex # pylint: disable=W0403

def create_broken_image(broken, dest):
    delete_if_exists(dest)

    os.symlink(broken, dest)

def pil_format_to_ext(pil_format):
    if 'PNG' == pil_format:
        return '.png'
    elif 'JPEG' == pil_format:
        return '.jpg'
    return None

def crop(filename, x=0, y=0, w=0, h=0):
    source = settings.UPLOADED_FILES_ROOT + filename
    dest = settings.READY_FILES_ROOT + filename

    if os.path.isfile(dest):
        print "Already done"
        return 0 # already done, skip

    if not os.path.isfile(source):
        print "Source image missing"
        return 1 # source image doesn't exist, can't crop it

    broken_file = settings.MEDIA_ROOT + 'img/broken'

    # Basic image validation
    try:
        img = Image.open(source)
    except:
        create_broken_image(broken_file + '.png', dest)
        print "Cannot open image"
        return 2
    ext = pil_format_to_ext(img.format)
    if not ext:
        create_broken_image(broken_file + ext, dest)
        print "Invalid extension"
        return 3
    try:
        img.verify()
    except:
        create_broken_image(broken_file + ext, dest)
        print "Image failed verification"
        return 2

    # Need to reopen the image after verify()
    img = Image.open(source)
    unused, unused, a, b = img.getbbox()

    if w == 0 and h == 0:
        w, h = a, b
        i = min(w, h)
        w, h = i, i
    elif w < 0 or x+w > a or h < 0 or y+h > b:
        raise ValueError('crop dimensions outside of original image bounding box')

    cropped = img.crop((x, y, x+w, y+h))
    cropped.load()

    # Resize the image only if it's larger than the specified max width.
    cropped_w, cropped_h = cropped.size
    max_w = settings.AVATAR_MAX_SIZE
    if cropped_w > max_w or cropped_h > max_w:
        cropped = cropped.resize((max_w, max_w), Image.ANTIALIAS)

    cropped.save(dest, img.format, quality=settings.JPEG_QUALITY)

    if 'JPEG' == img.format:
        if os.system("jpegoptim -q -p --strip-all %s" % dest) != 0:
            create_broken_image(broken_file + ext, dest)
            print "optimisation failed"
            return 4
    elif 'PNG' == img.format:
        if os.system("optipng -q -o9 -preserve %s" % dest) != 0:
            create_broken_image(broken_file + ext, dest)
            print "optimisation failed"
            return 4
    else:
        print "Unexpected error"
        return 5

    return 0

def main(argv=None):
    if argv is None:
        argv = sys.argv

    gearman_workload = sys.stdin.read()
    params = json.loads(gearman_workload)

    file_hash = params['file_hash']
    file_format = params['format']
    x = int(params['x'])
    y = int(params['y'])
    w = int(params['w'])
    h = int(params['h'])

    # Validate inputs
    if not is_hex(file_hash):
        return 1
    if file_format != 'jpg' and file_format != 'png':
        return 1

    filename = "%s.%s" % (file_hash, file_format)
    return_code = crop(filename, x, y, w, h)
    if return_code != 0:
        return return_code

    gm_client = libgearman.Client()
    for server in settings.GEARMAN_SERVERS:
        gm_client.add_server(server)

    params = {'file_hash' : file_hash, 'format': file_format}
    gm_client.do_background('ready2user', json.dumps(params))

    return 0

if __name__ == "__main__":
    sys.exit(main())
