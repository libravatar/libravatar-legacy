# Copyright (C) 2010  Francois Marier <francois@libravatar.org>
#                     Jonathan Harker <jon@jon.geek.nz>
#                     Brett Wilkins <bushido.katana@gmail.com>
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

from django.core.files import File
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect

from libravatar.account.external_photos import *
from libravatar.account.forms import AddEmailForm, PasswordResetForm, UploadPhotoForm
from libravatar.account.models import ConfirmedEmail, UnconfirmedEmail, Photo, password_reset_key
from libravatar import settings

import os
from StringIO import StringIO

@csrf_protect
def new(request):
    if settings.DISABLE_SIGNUP:
        return HttpResponseRedirect(settings.LOGIN_URL)
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save();

            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            if user is None:
                return HttpResponseRedirect(settings.LOGIN_URL)

            login(request, user)
            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = UserCreationForm()

    return render_to_response('account/new.html', { 'form': form },
                              context_instance=RequestContext(request))

@csrf_protect
def confirm_email(request):
    if not 'verification_key' in request.GET:
        return render_to_response('account/email_notconfirmed.html',
                                  context_instance=RequestContext(request))

    # be tolerant of extra crap added by mail clients
    key = request.GET['verification_key'].replace(' ', '')
    if len(key) != 64:
        return render_to_response('account/email_notconfirmed.html',
                                  context_instance=RequestContext(request))

    try:
        unconfirmed = UnconfirmedEmail.objects.get(verification_key=key)
    except UnconfirmedEmail.DoesNotExist:
        return render_to_response('account/email_notconfirmed.html',
                                  context_instance=RequestContext(request))

    # TODO: check for a reasonable expiration time
    confirmed = ConfirmedEmail()
    confirmed.user = unconfirmed.user
    confirmed.ip_address = request.META['REMOTE_ADDR']
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

    return render_to_response('account/email_confirmed.html',
                              {'email_id' : confirmed.id, 'photos' : external_photos},
                              context_instance=RequestContext(request))

@csrf_protect
def import_photo(request, user_id):
    if request.method == 'POST':
        if not 'email_id' in request.POST:
            return render_to_response('account/photos_notimported.html',
                                      context_instance=RequestContext(request))

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return render_to_response('account/photos_notimported.html',
                                      context_instance=RequestContext(request))
        try:
            email = ConfirmedEmail.objects.get(id=request.POST['email_id'])
        except ConfirmedEmail.DoesNotExist:
            return render_to_response('account/photos_notimported.html',
                                      context_instance=RequestContext(request))

        if int(user_id) != email.user_id:
            return render_to_response('account/photos_notimported.html',
                                      context_instance=RequestContext(request))


        photos_imported = False
        if 'photo_Identica' in request.POST:
            p = Photo()
            p.user = user
            p.ip_address = request.META['REMOTE_ADDR']
            if p.import_image('Identica', email.email):
                photos_imported = True

        if 'photo_Gravatar' in request.POST:
            p = Photo()
            p.user = user
            p.ip_address = request.META['REMOTE_ADDR']
            if p.import_image('Gravatar', email.email):
                photos_imported = True

        if photos_imported:
            return render_to_response('account/photos_imported.html',
                                      context_instance=RequestContext(request))
        else:
            return render_to_response('account/photos_notimported.html',
                                      context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

@login_required
def successfully_authenticated(request):
    if request.user.ldap_user:
        try:
            confirmed = ConfirmedEmail.objects.get(email=request.user.email)
        except ConfirmedEmail.DoesNotExist:
            confirmed = ConfirmedEmail()
            confirmed.user = request.user
            confirmed.email = request.user.email
            confirmed.save()

            # remove unconfirmed email address if necessary
            try:
                unconfirmed = UnconfirmedEmail.objects.get(email=request.user.email)
                unconfirmed.delete()
            except UnconfirmedEmail.DoesNotExist:
                pass

            # add photo to database, bung LDAP photo into the expected file
            photo_contents = request.user.ldap_user.attrs[settings.AUTH_LDAP_USER_PHOTO][0]
            fp = StringIO(photo_contents) # file pointer to in-memory string buffer
            image = File(fp)
            p = Photo()
            p.user = request.user
            p.save(image)
            return HttpResponseRedirect(reverse('libravatar.account.views.crop_photo', args=[p.id]))

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

@csrf_protect
@login_required
def profile(request):
    u = request.user
    confirmed = ConfirmedEmail.objects.filter(user=u).order_by('email')
    unconfirmed = UnconfirmedEmail.objects.filter(user=u).order_by('email')
    photos = Photo.objects.filter(user=u).order_by('add_date')
    max_photos = len(photos) >= settings.MAX_NUM_PHOTOS
    max_emails = len(unconfirmed) >= settings.MAX_NUM_UNCONFIRMED_EMAILS

    # force evaluation of the QuerySet objects
    list(confirmed)
    list(unconfirmed)
    list(photos)

    return render_to_response('account/profile.html',
                              {'confirmed_emails' : confirmed, 'unconfirmed_emails': unconfirmed,
                               'photos' : photos, 'max_photos' : max_photos, 'max_emails' : max_emails},
                              context_instance=RequestContext(request))

@csrf_protect
@login_required
def add_email(request):
    if request.method == 'POST':
        form = AddEmailForm(request.POST)
        if form.is_valid():
            if not form.save(request.user):
                return render_to_response('account/email_notadded.html',
                                          {'max_emails' : settings.MAX_NUM_UNCONFIRMED_EMAILS},
                                          context_instance=RequestContext(request))
            return HttpResponseRedirect(reverse('libravatar.account.views.profile'))
    else:
        form = AddEmailForm()

    return render_to_response('account/add_email.html', { 'form': form },
                              RequestContext(request))

@csrf_protect
@login_required
def remove_confirmed_email(request, email_id):
    if request.method == 'POST':
        try:
            email = ConfirmedEmail.objects.get(id=email_id, user=request.user)
        except ConfirmedEmail.DoesNotExist:
            return render_to_response('account/email_invalid.html',
                                      context_instance=RequestContext(request))

        email.delete()

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

@csrf_protect
@login_required
def remove_unconfirmed_email(request, email_id):
    if request.method == 'POST':
        try:
            email = UnconfirmedEmail.objects.get(id=email_id, user=request.user)
        except UnconfirmedEmail.DoesNotExist:
            return render_to_response('account/email_invalid.html', context_instance=RequestContext(request))

        email.delete()

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

@csrf_protect
@login_required
def upload_photo(request):
    num_photos = Photo.objects.filter(user=request.user).count()
    if num_photos >= settings.MAX_NUM_PHOTOS:
        return render_to_response('account/max_photos.html', context_instance=RequestContext(request))

    if request.method == 'POST':
        form = UploadPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo_data = request.FILES['photo']
            if photo_data.size > settings.MAX_PHOTO_SIZE:
                return render_to_response('account/photo_toobig.html', { 'max_size' : settings.MAX_PHOTO_SIZE },
                                          context_instance=RequestContext(request))

            photo = form.save(request.user, request.META['REMOTE_ADDR'], photo_data)
            return HttpResponseRedirect(reverse('libravatar.account.views.crop_photo', args=[photo.id]))
    else:
        form = UploadPhotoForm()

    return render_to_response('account/upload_photo.html', {'form': form, 'max_file_size' : settings.MAX_PHOTO_SIZE},
                              context_instance=RequestContext(request))

@csrf_protect
@login_required
def crop_photo(request, photo_id):
    try:
        photo = Photo.objects.get(id=photo_id, user=request.user)
    except Photo.DoesNotExist:
        return render_to_response('account/photo_invalid.html',
                                  context_instance=RequestContext(request))

    if request.method == 'POST':
        x = int(request.POST['x'])
        y = int(request.POST['y'])
        w = int(request.POST['w'])
        h = int(request.POST['h'])
        photo.crop(x, y, w, h)
        return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

    return render_to_response('account/crop_photo.html', {'photo': photo, 'needs_jquery':True, 'needs_jcrop':True},
                              context_instance=RequestContext(request))

@login_required
def auto_crop(request, photo_id):
    try:
        photo = Photo.objects.get(id=photo_id, user=request.user)
    except Photo.DoesNotExist:
        return render_to_response('account/photo_invalid.html',
                                  context_instance=RequestContext(request))

    photo.crop()
    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

@csrf_protect
@login_required
def delete_photo(request, photo_id):
    try:
        photo = Photo.objects.get(id=photo_id, user=request.user)
    except Photo.DoesNotExist:
        return render_to_response('account/photo_invalid.html', context_instance=RequestContext(request))

    if request.method == 'POST':
        photo.delete()
        return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

    return render_to_response('account/delete_photo.html', { 'photo': photo },
                              context_instance=RequestContext(request))

@csrf_protect
@login_required
def assign_photo(request, email_id):
    try:
        email = ConfirmedEmail.objects.get(id=email_id, user=request.user)
    except ConfirmedEmail.DoesNotExist:
        return render_to_response('account/email_invalid.html',
                                  context_instance=RequestContext(request))

    if request.method == 'POST':
        photo = None
        if 'photo_id' in request.POST and request.POST['photo_id']:
            try:
                photo = Photo.objects.get(id=request.POST['photo_id'], user=request.user)
            except Photo.DoesNotExist:
                return render_to_response('account/photo_invalid.html',
                                          context_instance=RequestContext(request))

        email.set_photo(photo)
        return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

    photos = Photo.objects.filter(user=request.user)
    list(photos) # force evaluation of the QuerySet
    return render_to_response('account/assign_photo.html', {'photos': photos, 'email': email},
                              context_instance=RequestContext(request))

@csrf_protect
def password_reset(request):
    if settings.DISABLE_SIGNUP:
        return HttpResponseRedirect(settings.LOGIN_URL)
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save();
            return render_to_response('account/password_reset_submitted.html',
                                      {'form': form, 'support_email' : settings.SUPPORT_EMAIL},
                                      context_instance=RequestContext(request))
    else:
        form = PasswordResetForm()

    return render_to_response('account/password_reset.html', { 'form': form },
                              context_instance=RequestContext(request))

@csrf_protect
def password_reset_confirm(request):
    if settings.DISABLE_SIGNUP:
        return HttpResponseRedirect(settings.LOGIN_URL)

    verification_key = None
    email_address = None

    if 'verification_key' in request.GET and request.GET['verification_key']:
        verification_key = request.GET['verification_key']

    if 'email_address' in request.GET and request.GET['email_address']:
        email_address = request.GET['email_address']

    # Note: all validation errors return the same error message to
    # avoid leaking information as to the existence or not of
    # particular email addresses on the system

    if not verification_key or not email_address:
        return render_to_response('account/reset_invalidparams.html',
                                  context_instance=RequestContext(request))

    if len(verification_key) < 64 or len(verification_key) > 64 or len(email_address) < 3:
        return render_to_response('account/reset_invalidparams.html',
                                  context_instance=RequestContext(request))

    try:
        email = ConfirmedEmail.objects.get(email=email_address)
    except ConfirmedEmail.DoesNotExist:
        return render_to_response('account/reset_invalidparams.html',
                                  context_instance=RequestContext(request))

    user = email.user
    expected_key = password_reset_key(user)

    if verification_key != expected_key:
        return render_to_response('account/reset_invalidparams.html',
                                  context_instance=RequestContext(request))

    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            return render_to_response('account/password_change_done.html',
                                      context_instance=RequestContext(request))
    else:
        form = SetPasswordForm(user)

    return render_to_response('account/password_change.html', {'form' : form,
                              'verification_key' : verification_key, 'email_address' : email_address},
                              context_instance=RequestContext(request))
