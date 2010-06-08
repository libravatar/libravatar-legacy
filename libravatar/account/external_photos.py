# Copyright (C) 2010  Francois Marier <francois@libravatar.org>
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

from urllib2 import urlopen, HTTPError
from hashlib import md5
import xml.dom.minidom as minidom

def identica_photo(email):
    image_url = ''
    screen_name = ''

    try:
        fh = urlopen('http://identi.ca/api/users/show.xml?email=' + email)
    except HTTPError:
        return False

    contents = fh.read()
    response = minidom.parseString(contents)
    
    elements = response.getElementsByTagName('profile_image_url')
    for element in elements:
        textnode = element.firstChild
        if minidom.Node.TEXT_NODE == textnode.nodeType:
            image_url = textnode.nodeValue

    elements = response.getElementsByTagName('screen_name')
    for element in elements:
        textnode = element.firstChild
        if minidom.Node.TEXT_NODE == textnode.nodeType:
            screen_name = textnode.nodeValue

    # get the larger-format image from the profile page
    if image_url:
        image_url = image_url.replace('-48-', '-96-')

    if image_url and screen_name:
        return { 'image_url' : image_url, 'width' : 96, 'height' : 96,
                 'service_url' : 'http://identi.ca/' + screen_name, 'service_name' : 'Identica' }

    return False

def gravatar_photo(email):
    image_url = 'http://www.gravatar.com/avatar/' + md5(email.lower()).hexdigest() + '?s=80&d=404'

    try:
        fh = urlopen(image_url)
    except HTTPError:
        return False

    return { 'image_url' : image_url, 'width' : 80, 'height' : 80, 'service_name' : 'Gravatar' }
