# Copyright (C) 2010, 2011  Francois Marier <francois@libravatar.org>
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

from urllib2 import urlopen, HTTPError, URLError
import hashlib

URL_TIMEOUT = 5  # in seconds


def gravatar_photo(email):
    hash_object = hashlib.new('md5')
    hash_object.update(email.lower())
    thumbnail_url = 'https://secure.gravatar.com/avatar/' + hash_object.hexdigest() + '?s=80&d=404'
    image_url = 'https://secure.gravatar.com/avatar/' + hash_object.hexdigest() + '?s=512&d=404'

    # Will redirect to the public profile URL if it exists
    service_url = 'http://www.gravatar.com/' + hash_object.hexdigest()

    try:
        urlopen(image_url, timeout=URL_TIMEOUT)
    except HTTPError as e:
        if e.code != 404 and e.code != 503:
            print 'Gravatar fetch failed with an unexpected %s HTTP error' % e.code
        return False
    except URLError as e:
        print 'Gravatar fetch failed: %s' % e.reason
        return False

    return {'thumbnail_url': thumbnail_url, 'image_url': image_url, 'width': 80,
            'height': 80, 'service_url': service_url, 'service_name': 'Gravatar'}
