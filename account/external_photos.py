from urllib2 import urlopen, HTTPError
from hashlib import md5
import xml.dom.minidom as minidom

def identica_photo(email):
    return False # currently disabled because it's too slow
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

