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

import DNS
from hashlib import md5, sha1, sha256

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from libravatar.public.views import lookup_avatar_server
from libravatar.tools.forms import CheckForm, CheckDomainForm

def check(request):
    data = None
    if (request.POST):
        form = CheckForm(request.POST)
        if form.is_valid():
            data = {}

            email = form.cleaned_data['email']
            data['md5'] = md5(email.strip().lower()).hexdigest()
            data['sha1'] = sha1(email.strip().lower()).hexdigest()
            data['sha256'] = sha256(email.strip().lower()).hexdigest()

            domain = email.split('@')[-1]
            data['query_string'] = '?domain=' + domain
            print domain

            if len(form.cleaned_data['not_found']) > 0:
                if len(data['query_string']) > 0:
                    data['query_string'] += '&'
                else:
                    data['query_string'] = '?'
                
                data['query_string'] += 'd=' + form.cleaned_data['not_found']

            if form.cleaned_data['size']:
                if len(data['query_string']) > 0:
                    data['query_string'] += '&'
                else:
                    data['query_string'] = '?'

                data['query_string'] += 's=%s' % form.cleaned_data['size']
    else:
        form = CheckForm()

    return render_to_response('tools/check.html', {'form': form, 'data' : data},
                              context_instance=RequestContext(request))

def lookup_ip_address(hostname, ipv6):
    """
    Try to get IPv4 or IPv6 addresses for the given hostname
    """

    DNS.DiscoverNameServers()
    try:
        if ipv6:
            dns_request = DNS.Request(name=hostname, qtype=DNS.Type.AAAA).req()
        else:
            dns_request = DNS.Request(name=hostname, qtype=DNS.Type.A).req()
    except DNS.DNSError as message:
        print "DNS Error: %s" % message
        return None

    if dns_request.header['status'] != 'NOERROR':
        print "DNS Error: status=%s" % dns_request.header['status']
        return None

    for answer in dns_request.answers:
        if (not 'data' in answer) or (not answer['data']):
            continue

        # TODO: fix the display (binary?) of IPv6 addresses
        return answer['data']

    return None

def check_domain(request):
    data = None
    if (request.POST):
        form = CheckDomainForm(request.POST)
        if form.is_valid():
            data = {}
            domain = form.cleaned_data['domain']
            data['avatar_server_http'] = lookup_avatar_server(domain, False)
            if data['avatar_server_http']:
                data['avatar_server_http_ipv4'] = lookup_ip_address(data['avatar_server_http'], False)
            data['avatar_server_https'] = lookup_avatar_server(domain, True)
            if data['avatar_server_https']:
                data['avatar_server_https_ipv4'] = lookup_ip_address(data['avatar_server_https'], False)
    else:
        form = CheckDomainForm()

    return render_to_response('tools/check_domain.html', {'form': form, 'data' : data},
                              context_instance=RequestContext(request))
