# Copyright (C) 2010  Brett Wilkins <bushido.katana@gmail.com>
#                     Francois Marier <francois@libravatar.org>
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

import os
import Image

from libravatar import settings

def crop(filename, x=0, y=0, w=0, h=0):
    img = Image.open(filename)
    junk, junk, a, b = img.getbbox()

    if w == 0 and h == 0:
        w,h = a,b
        i = min(w,h)
        w,h = i,i
    elif w < 0 or x+w > a or h < 0 or y+h > b:
        raise ValueError('crop dimensions outside of original image bounding box')

    cropped = img.crop((x, y, x+w, y+h))
    cropped.load()
    cropped.save(filename, img.format)

def auto_resize(filename, max_w=settings.AVATAR_MAX_SIZE):
    """
    Resize the image only if it's larger than the specified max width.
    """
    img = Image.open(filename)

    img_w, img_h = img.size
    if img_w <= max_w and img_h <= max_w:
        return # nothing to do, image is small enough

    resized_img = img.resize((max_w, max_w))
    resized_img.save(filename, img.format)

def resize(filename, w, output_filename=None):
    img = Image.open(filename)

    if not output_filename:
        output_filename = filename

    resized_img = img.resize((w, w))
    resized_img.save(output_filename, img.format)
    return img.format

def resized_avatar(email_hash, size):
    original_filename = settings.AVATAR_ROOT + email_hash

    output_dir = settings.AVATAR_ROOT + '/%s' % size
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    resized_filename = '%s/%s' % (output_dir, email_hash)

    # Save resized image to disk
    format = resize(original_filename, size, resized_filename)

    # TODO: use find -inum on the original inode to find other hashes
    # then hardlink the resized image to the other hashes

    return (resized_filename, format)
