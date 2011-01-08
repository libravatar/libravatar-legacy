# Copyright (C) 2010  Francois Marier <francois@libravatar.org>
#                     Jonathan Harker <jon@jon.geek.nz>
#                     Brett Wilkins <bushido.katana@gmail.com>
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

import DNS
import os
import Image
import urllib

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from libravatar import settings

def mimetype_format(pil_format):
    if 'JPEG' == pil_format:
        return 'image/jpeg'
    elif 'PNG' == pil_format:
        return 'image/png'

    print "ERROR: got invalid file format from PIL: %s" % pil_format
    return 'image/jpeg'

def home(request):
    return render_to_response('public/home.html',
                              context_instance=RequestContext(request))

def lookup_avatar_server(domain, https):
    """
    Extract the avatar server from an SRV record in the DNS zone

    The SRV records should look like this:

       _avatars._tcp.example.com.     IN SRV 0 0 80  avatars.example.com
       _avatars-sec._tcp.example.com. IN SRV 0 0 443 avatars.example.com
    """

    service_name = None
    if https:
        service_name = "_avatars-sec._tcp.%s" % domain
    else:
        service_name = "_avatars._tcp.%s" % domain

    DNS.DiscoverNameServers()
    try:
        dns_request = DNS.Request(name=service_name, qtype='SRV').req()
    except DNS.DNSError as message:
        print "DNS Error: %s" % message
        return None

    if dns_request.header['status'] != 'NOERROR':
        print "DNS Error: status=%s" % dns_request.header['status']
        return None

    for answer in dns_request.answers:
        if (not 'data' in answer) or (not answer['data']):
            continue

        # TODO: implement priority and weight
        priority = int(answer['data'][0])
        weight = int(answer['data'][1])
        port = int(answer['data'][2])
        target = answer['data'][3]
        if (https and port != 443) or (not https and port != 80):
             "%s:%s" % (target, port)
        else:
            return target

    return None

def resolve(request):
    if request.method == 'POST':
        return render_to_response('public/nopost.html',
                                  context_instance=RequestContext(request))

    if not 'email_hash' in request.GET:
        return render_to_response('public/nohash.html',
                                  context_instance=RequestContext(request))

    # Maintain the default redirection that was specified
    not_found = ''
    if 'd' in request.GET:
        not_found = '?d=%s' % urllib.quote(request.GET['d'])
    elif 'default' in request.GET:
        not_found = '?d=%s' % urllib.quote(request.GET['default'])

    email_hash = request.GET['email_hash']
    avatar_server = settings.SITE_URL

    # Check to see if we need to delegate to another avatar server
    if 'domain' in request.GET:
        delegation_server = lookup_avatar_server(request.GET['domain'], False)
        if delegation_server:
            avatar_server = delegation_server
            # redirect first to 
            not_found = '?d=' + urllib.quote(settings.AVATAR_URL + email_hash + not_found)

    final_url = avatar_server + '/avatar/' + email_hash + not_found
    return HttpResponseRedirect(final_url)

def avatar_exists(email_hash, size):
    filename = settings.AVATAR_ROOT + '/%s/%s' % (size, email_hash)
    return os.path.isfile(filename)

def resized_avatar(email_hash, size):
    original_filename = settings.AVATAR_ROOT + email_hash

    output_dir = settings.AVATAR_ROOT + '/%s' % size
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    resized_filename = '%s/%s' % (output_dir, email_hash)

    # Save resized image to disk
    original_img = Image.open(original_filename)
    resized_img = original_img.resize((size, size), Image.ANTIALIAS)
    resized_img.save(resized_filename, original_img.format)

    # TODO: use find -inum on the original inode to find other hashes
    # then hardlink the resized image to the other hashes

    return (resized_filename, original_img.format)

def resize(request):
    if request.method == 'POST':
        return render_to_response('public/nopost.html',
                                  context_instance=RequestContext(request))

    if not 'email_hash' in request.GET:
        return render_to_response('public/nohash.html',
                                  context_instance=RequestContext(request))
    email_hash = request.GET['email_hash']

    size = settings.AVATAR_DEFAULT_SIZE
    if 'size' in request.GET:
        try:
            size = int(request.GET['size'])
        except ValueError:
            return render_to_response('public/resize_notnumeric.html',
                                      {'min_size' : settings.AVATAR_MIN_SIZE, 'max_size' : settings.AVATAR_MAX_SIZE},
                                      context_instance=RequestContext(request))

        size = max(size, settings.AVATAR_MIN_SIZE)
        size = min(size, settings.AVATAR_MAX_SIZE)

    if avatar_exists(email_hash, size):
        return HttpResponseRedirect(settings.AVATAR_URL + email_hash + '?s=%s' % size)

    # Add a note to the logs to keep track of frequently requested sizes
    print '[RESIZE] %s px' % size

    (resized_filename, format) = resized_avatar(email_hash, size)

    # Serve resized image
    response = HttpResponse(mimetype=mimetype_format(format))
    with open(resized_filename, 'rb') as resized_img:
        response.write(resized_img.read())
        resized_img.close()

    return response
