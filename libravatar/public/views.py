# Copyright (C) 2010  Francois Marier <francois@libravatar.org>
#                     Jonathan Harker <jon@jon.geek.nz>
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

import urllib

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from libravatar import settings

def home(request):
    return render_to_response('public/home.html',
                              context_instance=RequestContext(request))

def lookup_avatar_server(domain, https):
    """
    Extract the avatar server from a TXT record in the DNS zone

    The TXT record should look like this:

       "v=avatars1 http://avatars.libravatar.org"
    """

    if https:
        return None # Not implemented

    import DNS
    DNS.DiscoverNameServers()

    dns_request = DNS.Request(name=domain, qtype='TXT').req()

    if dns_request.header['status'] != 'NOERROR':
        return None

    for answer in dns_request.answers:
        if (not 'data' in answer) or (not answer['data']):
            continue

        txt_version = 'v=' + settings.TXT_VERSION
        data = answer['data'][0]
        if data.startswith(txt_version):
            i = len(txt_version) + 1
            if len(data) > i:
                return data[i:] # hostname

    return None

def resolve(request):
    if request.method == 'POST':
        return render_to_response('public/resolve_nopost.html',
                                  context_instance=RequestContext(request))

    if not 'email_hash' in request.GET:
        return render_to_response('public/resolve_nohash.html',
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
