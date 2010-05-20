from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response

from libravatar.account.forms import AddEmailForm, UploadPhotoForm
from libravatar.account.models import ConfirmedEmail, UnconfirmedEmail, Photo
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
        return render_to_response('account/email_notconfirmed.html')
    try:
        unconfirmed = UnconfirmedEmail.objects.get(verification_key=request.GET['verification_key'])
    except UnconfirmedEmail.DoesNotExist:
        return render_to_response('account/email_notconfirmed.html')
    else:
        # TODO: check for a reasonable expiration time
        confirmed = ConfirmedEmail()
        confirmed.user = unconfirmed.user
        confirmed.email = unconfirmed.email
        confirmed.save()

        unconfirmed.delete()
        return render_to_response('account/email_confirmed.html')

@login_required
def profile(request):
    u = request.user
    confirmed = ConfirmedEmail.objects.filter(user=u)
    unconfirmed = UnconfirmedEmail.objects.filter(user=u)
    photos = Photo.objects.filter(user=u)
    return render_to_response('account/profile.html',
        { 'user': u, 'confirmed_emails' : confirmed, 'unconfirmed_emails': unconfirmed, 'photos' : photos })

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

@login_required
def upload_photo(request):
    if request.method == 'POST':
        form = UploadPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(request.user, request.FILES['photo'])
            return HttpResponseRedirect(reverse('libravatar.account.views.profile'))
    else:
        form = UploadPhotoForm()

    return render_to_response('account/upload_photo.html', { 'form': form })
