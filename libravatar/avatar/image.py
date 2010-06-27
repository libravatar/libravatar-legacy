# Copyright (C) 2010  Brett Wilkins <bushido.katana@gmail.com>
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
    try:
        img = Image.open(image)
    except:
        return
    junk,junk,a,b=img.getbbox()
    if w == 0 and h == 0:
        w,h = a,b
        i = min(w,h)
        w,h = i,i
    else:
        if w < 0 or x+w > a or h < 0 or y+h > b:
            raise ValueError("crop dimensions outside of original image bounding box")
    cropped = img.crop((x,y,x+w,y+h)) 
    cropped.load()
    cropped.save(image)

def resize(image,w=512,h=None):
    try:
        img = Image.open(image)
    except:
        return
    if not h:
        h=w
    img.resize((w,h))
    img.save(image)
