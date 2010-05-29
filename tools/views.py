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
