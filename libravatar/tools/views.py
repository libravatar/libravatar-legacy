# Copyright (C) 2010, 2011, 2013  Francois Marier <francois@libravatar.org>
#               2010  Jonathan Harker <jon@jon.geek.nz>
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
from hashlib import md5, sha256
from socket import inet_ntop, AF_INET6
from urlparse import urlsplit, urlunsplit

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
            openid = form.cleaned_data['openid']

            if email:
                lowercase_value = email.strip().lower()
                domain = email.split('@')[-1]
                data['md5'] = md5(lowercase_value).hexdigest()
            else:
                url = urlsplit(openid.strip())
                lowercase_value = urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path, url.query, url.fragment))  # pylint: disable=E1103
                domain = url.netloc  # pylint: disable=E1103

            data['sha256'] = sha256(lowercase_value).hexdigest()
            data['query_string'] = '?domain=' + domain

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

    return render_to_response('tools/check.html', {'form': form, 'data': data},
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
        print "DNS Error: %s (%s)" % (message, hostname)
        return None

    if dns_request.header['status'] != 'NOERROR':
        print "DNS Error: status=%s (%s)" % (dns_request.header['status'], hostname)
        return None

    for answer in dns_request.answers:
        if (not 'data' in answer) or (not answer['data']):
            continue
        if (ipv6 and answer['typename'] != 'AAAA') or (not ipv6 and answer['typename'] != 'A'):
            continue  # skip CNAME records

        if ipv6:
            return inet_ntop(AF_INET6, answer['data'])
        else:
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
                data['avatar_server_http_ipv6'] = lookup_ip_address(data['avatar_server_http'], True)
            data['avatar_server_https'] = lookup_avatar_server(domain, True)
            if data['avatar_server_https']:
                data['avatar_server_https_ipv4'] = lookup_ip_address(data['avatar_server_https'], False)
                data['avatar_server_https_ipv6'] = lookup_ip_address(data['avatar_server_https'], True)
    else:
        form = CheckDomainForm()

    return render_to_response('tools/check_domain.html', {'form': form, 'data': data},
                              context_instance=RequestContext(request))
