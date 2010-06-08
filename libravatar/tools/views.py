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

from hashlib import md5, sha1, sha256

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response

from libravatar.tools.forms import CheckForm

def check(request):
    data = None
    if (request.POST):
        form = CheckForm(request.POST)

        if 'email' in request.POST:
            email = request.POST['email']

            data = {}
            data['md5'] = md5(email.lower()).hexdigest()
            data['sha1'] = sha1(email.lower()).hexdigest()
            data['sha256'] = sha256(email.lower()).hexdigest()
    else:
        form = CheckForm()

    return render_to_response('tools/check.html', {'form': form, 'data' : data})
