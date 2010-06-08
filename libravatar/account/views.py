from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response

from libravatar.account.external_photos import *
from libravatar.account.forms import AddEmailForm, UploadPhotoForm
from libravatar.account.models import ConfirmedEmail, UnconfirmedEmail, Photo
from libravatar.settings import LOGIN_URL, LOGIN_REDIRECT_URL

MAX_NUM_PHOTOS = 5

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

    # be tolerant of extra crap added by mail clients
    key = request.GET['verification_key'].replace(' ', '')
    if len(key) != 64:
        return render_to_response('account/email_notconfirmed.html')

    try:
        unconfirmed = UnconfirmedEmail.objects.get(verification_key=key)
    except UnconfirmedEmail.DoesNotExist:
        return render_to_response('account/email_notconfirmed.html')

    # TODO: check for a reasonable expiration time
    confirmed = ConfirmedEmail()
    confirmed.user = unconfirmed.user
    confirmed.email = unconfirmed.email
    confirmed.save()

    unconfirmed.delete()

    external_photos = []

    identica = identica_photo(confirmed.email)
    if identica:
        external_photos.append(identica)
    gravatar = gravatar_photo(confirmed.email)
    if gravatar:
        external_photos.append(gravatar)

    return render_to_response('account/email_confirmed.html', {'user' : request.user,
                              'email_id' : confirmed.id, 'photos' : external_photos})

def import_photo(request, user_id):
    if request.method == 'POST':
        if not 'email_id' in request.POST:
            return render_to_response('account/photos_notimported.html')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return render_to_response('account/photos_notimported.html')
        try:
            email = ConfirmedEmail.objects.get(id=request.POST['email_id'])
        except ConfirmedEmail.DoesNotExist:
            return render_to_response('account/photos_notimported.html')

        if user.id != email.user.id:
            return render_to_response('account/photos_notimported.html')

        photos_imported = False
        if 'photo_Identica' in request.POST:
            p = Photo()
            p.user = user
            if p.import_image('Identica', email.email):
                photos_imported = True

        if 'photo_Gravatar' in request.POST:
            print 'gravatar'
            p = Photo()
            p.user = user
            if p.import_image('Gravatar', email.email):
                photos_imported = True

        if photos_imported:
            return render_to_response('account/photos_imported.html')
        else:
            return render_to_response('account/photos_notimported.html')

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

@login_required
def profile(request):
    u = request.user
    confirmed = ConfirmedEmail.objects.filter(user=u)
    unconfirmed = UnconfirmedEmail.objects.filter(user=u)
    photos = Photo.objects.filter(user=u)
    max_photos = len(photos) >= MAX_NUM_PHOTOS
    return render_to_response('account/profile.html',
        { 'user': u, 'confirmed_emails' : confirmed, 'unconfirmed_emails': unconfirmed,
          'photos' : photos, 'max_photos' : max_photos })

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
def remove_confirmed_email(request, email_id):
    if request.method == 'POST':
        try:
            email = ConfirmedEmail.objects.get(id=email_id)
        except ConfirmedEmail.DoesNotExist:
            return render_to_response('account/email_invalid.html')

        if email.user.id == request.user.id:
            email.delete()
        else:
            return render_to_response('account/email_notowner.html')

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

@login_required
def remove_unconfirmed_email(request, email_id):
    if request.method == 'POST':
        try:
            email = UnconfirmedEmail.objects.get(id=email_id)
        except UnconfirmedEmail.DoesNotExist:
            return render_to_response('account/email_invalid.html')

        if email.user.id == request.user.id:
            email.delete()
        else:
            return render_to_response('account/email_notowner.html')

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

@login_required
def upload_photo(request):
    num_photos = Photo.objects.filter(user=request.user).count()
    if num_photos >= MAX_NUM_PHOTOS:
        return render_to_response('account/max_photos.html')

    if request.method == 'POST':
        form = UploadPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(request.user, request.FILES['photo'])
            return HttpResponseRedirect(reverse('libravatar.account.views.profile'))
    else:
        form = UploadPhotoForm()

    return render_to_response('account/upload_photo.html', { 'form': form })

@login_required
def delete_photo(request, photo_id):
    try:
        photo = Photo.objects.get(id=photo_id)
    except Photo.DoesNotExist:
        return render_to_response('account/photo_invalid.html')

    if request.method == 'POST':
        if photo.user.id != request.user.id:
            return render_to_response('account/photo_notowner.html')
        photo.delete()
        return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

    return render_to_response('account/delete_photo.html', { 'photo': photo })

@login_required
def assign_photo(request, email_id):
    try:
        email = ConfirmedEmail.objects.get(id=email_id)
    except ConfirmedEmail.DoesNotExist:
        return render_to_response('account/email_invalid.html')

    if email.user.id != request.user.id:
        return render_to_response('account/email_notowner.html')

    if request.method == 'POST':
        photo = None
        if 'photo_id' in request.POST and request.POST['photo_id']:
            try:
                photo = Photo.objects.get(id=request.POST['photo_id'])
            except Photo.DoesNotExist:
                return render_to_response('account/photo_invalid.html')

        if photo and (photo.user.id != request.user.id):
            return render_to_response('account/photo_notowner.html')

        email.set_photo(photo)
        return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

    photos = Photo.objects.filter(user=request.user)
    return render_to_response('account/assign_photo.html', {'photos': photos, 'email': email})