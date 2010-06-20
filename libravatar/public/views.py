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

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from libravatar import settings

def home(request):
    return render_to_response('public/home.html',
                              context_instance=RequestContext(request))

def lookup_avatar_server(domain):
    """
    Extract the avatar server from a TXT record in the DNS zone

    The TXT record should look like this:

       "v=avatars1 http://avatars.libravatar.org"
    """

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

    email_hash = request.GET['email_hash']
    avatar_server = settings.SITE_URL

    # Check to see if we need to delegate to another avatar server
    if 'domain' in request.GET:
        delegation_server = lookup_avatar_server(request.GET['domain'])
        if delegation_server:
            avatar_server = delegation_server

    return HttpResponseRedirect(avatar_server + '/avatar/' + email_hash)
