from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response

from libravatar.account.forms import AddEmailForm
from libravatar.account.models import ConfirmedEmail, UnconfirmedEmail
from libravatar.settings import LOGIN_URL, LOGIN_REDIRECT_URL

def new(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save();

            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            if user is None:
                return HttpResponseRedirect(LOGIN_URL)

            login(request, user)
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    else:
        form = UserCreationForm()

    return render_to_response('account/new.html', { 'form': form })

def confirm_email(request):
    if not 'verification_key' in request.GET:
        return HttpResponse('TODO: missing verification key')
    try:
        unconfirmed = UnconfirmedEmail.objects.get(verification_key=request.GET['verification_key'])
    except UnconfirmedEmail.DoesNotExist:
        return HttpResponse('TODO: NOT confirmed')
    else:
        # TODO: check for a reasonable expiration time
        confirmed = ConfirmedEmail()
        confirmed.user = unconfirmed.user
        confirmed.email = unconfirmed.email
        confirmed.save()

        unconfirmed.delete()
        return HttpResponse('TODO: confirmed')

@login_required
def profile(request):
    u = request.user
    confirmed = ConfirmedEmail.objects.filter(user=u)
    unconfirmed = UnconfirmedEmail.objects.filter(user=u)
    return render_to_response('account/profile.html',
        { 'user': u, 'confirmed_emails' : confirmed, 'unconfirmed_emails': unconfirmed })

@login_required
def add_email(request):
    if request.method == 'POST':
        form = AddEmailForm(request.POST)
        if form.is_valid():
            form.save(request.user);
            return HttpResponseRedirect(reverse('libravatar.account.views.profile'))
    else:
        form = AddEmailForm()

    return render_to_response('account/add_email.html', { 'form': form })
