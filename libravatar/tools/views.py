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

            data['query_string'] = ''
            if len(form.cleaned_data['domain']) > 0:
                data['query_string'] = '?domain=' + form.cleaned_data['domain']
            if len(form.cleaned_data['not_found']) > 0:
                if len(data['query_string']) > 0:
                    data['query_string'] += '&'
                else:
                    data['query_string'] = '?'
                
                data['query_string'] += 'd=' + form.cleaned_data['not_found']
    else:
        form = CheckForm()

    return render_to_response('tools/check.html', {'form': form, 'data' : data},
                              context_instance=RequestContext(request))

def check_domain(request):
    data = None
    if (request.POST):
        form = CheckDomainForm(request.POST)
        if form.is_valid():
            data = {}
            domain = form.cleaned_data['domain']
            data['avatar_server_http'] = lookup_avatar_server(domain, False)
            data['avatar_server_https'] = lookup_avatar_server(domain, True)
    else:
        form = CheckDomainForm()

    return render_to_response('tools/check_domain.html', {'form': form, 'data' : data},
                              context_instance=RequestContext(request))
