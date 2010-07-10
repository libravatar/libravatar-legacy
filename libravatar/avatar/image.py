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

import Image

def crop(image,x=0,y=0,w=0,h=0):
    img = Image.open(image)
    junk, junk, a, b = img.getbbox()

    if w == 0 and h == 0:
        w,h = a,b
        i = min(w,h)
        w,h = i,i
    elif w < 0 or x+w > a or h < 0 or y+h > b:
        raise ValueError("crop dimensions outside of original image bounding box")

    cropped = img.crop((x,y,x+w,y+h))
    cropped.load()
    cropped.save(image)

def resize(image,w,h=None):
    img = Image.open(image)

    image_w, image_h = img.size
    w = min(w, image_w)
    h = min(h, image_h)

    if not h:
        h=w

    resized_img = img.resize((w, h))
    resized_img.save(image)
