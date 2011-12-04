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
import subprocess
import sys

# pylint: disable=W0403
import settings
from utils import create_logger, delete_if_exists, is_hex

logger = create_logger('cropresize')

MAX_PIXELS = 5000


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
        logger.info('Already done')
        return 0  # already done, skip

    if not os.path.isfile(source):
        logger.error('Source image missing')
        return 1  # source image doesn't exist, can't crop it

    broken_file = settings.MEDIA_ROOT + 'img/broken'

    # Basic image validation
    try:
        img = Image.open(source)
    except:
        create_broken_image(broken_file + '.png', dest)
        logger.error('Cannot open image')
        return 2
    ext = pil_format_to_ext(img.format)
    if not ext:
        create_broken_image(broken_file + ext, dest)
        logger.error('Invalid extension')
        return 3
    try:
        img.verify()
    except:
        create_broken_image(broken_file + ext, dest)
        logger.error('Image failed verification')
        return 2

    # Need to reopen the image after verify()
    img = Image.open(source)
    a, b = img.size
    if a > MAX_PIXELS or b > MAX_PIXELS:
        logger.error('Image dimensions are too big (max: %s x %s)' % (MAX_PIXELS, MAX_PIXELS))
        return 6

    if w == 0 and h == 0:
        w, h = a, b
        i = min(w, h)
        w, h = i, i
    elif w < 0 or (x + w) > a or h < 0 or (y + h) > b:
        logger.error('Crop dimensions outside of original image bounding box')
        return 6

    cropped = img.crop((x, y, x + w, y + h))
    cropped.load()

    # Resize the image only if it's larger than the specified max width.
    cropped_w, cropped_h = cropped.size
    max_w = settings.AVATAR_MAX_SIZE
    if cropped_w > max_w or cropped_h > max_w:
        cropped = cropped.resize((max_w, max_w), Image.ANTIALIAS)

    cropped.save(dest, img.format, quality=settings.JPEG_QUALITY)

    return optimize_image(dest, img.format, ext, broken_file)


def optimize_image(dest, img_format, ext, broken_file):
    if 'JPEG' == img_format:
        process = subprocess.Popen(['jpegoptim', '-p', '--strip-all', dest], stdout=subprocess.PIPE)
        if process.wait() != 0:
            create_broken_image(broken_file + ext, dest)
            logger.error('JPEG optimisation failed: %s' % process.communicate()[0])
            return 4
    elif 'PNG' == img_format:
        process = subprocess.Popen(['pngcrush', '-rem', 'gAMA', '-rem', 'alla', '-rem', 'text', dest, dest + '.tmp'], stdout=subprocess.PIPE)
        if process.wait() != 0:
            delete_if_exists(dest + '.tmp')
            create_broken_image(broken_file + ext, dest)
            logger.error('PNG optimisation (pngcrush) failed: %s' % process.communicate()[0])
            return 4
        delete_if_exists(dest)
        process = subprocess.Popen(['optipng', '-o9', '-preserve', '--force', '-out', dest, dest + '.tmp'], stdout=subprocess.PIPE)
        if process.wait() != 0:
            delete_if_exists(dest + '.tmp')
            create_broken_image(broken_file + ext, dest)
            logger.error('PNG optimisation (optipng) failed: %s' % process.communicate()[0])
            return 4
        delete_if_exists(dest + '.tmp')
        process = subprocess.Popen(['advpng', '--recompress', '--shrink-insane', dest], stdout=subprocess.PIPE)
        if process.wait() != 0:
            create_broken_image(broken_file + ext, dest)
            logger.error('PNG optimisation (advpng) failed: %s' % process.communicate()[0])
            return 4
    else:
        logger.error('Unexpected error while cropping')
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
        logger.error('file_hash is not a hexadecimal value')
        return 1
    if file_format != 'jpg' and file_format != 'png':
        logger.error('file_format is not recognized')
        return 1

    filename = "%s.%s" % (file_hash, file_format)
    return_code = crop(filename, x, y, w, h)
    if return_code != 0:
        return return_code

    gm_client = libgearman.Client()
    for server in settings.GEARMAN_SERVERS:
        gm_client.add_server(server)

    params = {'file_hash': file_hash, 'format': file_format}
    gm_client.do_background('ready2user', json.dumps(params))

    return 0

if __name__ == "__main__":
    sys.exit(main())
