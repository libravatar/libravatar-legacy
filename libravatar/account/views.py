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

from django.core.files import File
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from libravatar.account.external_photos import *
from libravatar.account.forms import AddEmailForm, UploadPhotoForm
from libravatar.account.models import ConfirmedEmail, UnconfirmedEmail, Photo
from libravatar import settings

import Image
import os
from StringIO import StringIO

MAX_NUM_PHOTOS = 5

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

        if user.id != email.user.id:
            return render_to_response('account/photos_notimported.html',
                                      context_instance=RequestContext(request))

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

            # assign photo to the email address
            confirmed.set_photo(p)

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

@login_required
def profile(request):
    u = request.user
    confirmed = ConfirmedEmail.objects.filter(user=u)
    unconfirmed = UnconfirmedEmail.objects.filter(user=u)
    photos = Photo.objects.filter(user=u)
    max_photos = len(photos) >= MAX_NUM_PHOTOS
    return render_to_response('account/profile.html',
        { 'confirmed_emails' : confirmed, 'unconfirmed_emails': unconfirmed,
          'photos' : photos, 'max_photos' : max_photos},
        context_instance=RequestContext(request))

@login_required
def add_email(request):
    if request.method == 'POST':
        form = AddEmailForm(request.POST)
        if form.is_valid():
            form.save(request.user);
            return HttpResponseRedirect(reverse('libravatar.account.views.profile'))
    else:
        form = AddEmailForm()

    return render_to_response('account/add_email.html', { 'form': form },
                              RequestContext(request))

@login_required
def remove_confirmed_email(request, email_id):
    if request.method == 'POST':
        try:
            email = ConfirmedEmail.objects.get(id=email_id)
        except ConfirmedEmail.DoesNotExist:
            return render_to_response('account/email_invalid.html',
                                      context_instance=RequestContext(request))

        if email.user.id == request.user.id:
            email.delete()
        else:
            return render_to_response('account/email_notowner.html',
                                      context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

@login_required
def remove_unconfirmed_email(request, email_id):
    if request.method == 'POST':
        try:
            email = UnconfirmedEmail.objects.get(id=email_id)
        except UnconfirmedEmail.DoesNotExist:
            return render_to_response('account/email_invalid.html', context_instance=RequestContext(request))

        if email.user.id == request.user.id:
            email.delete()
        else:
            return render_to_response('account/email_notowner.html', context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

@login_required
def upload_photo(request):
    num_photos = Photo.objects.filter(user=request.user).count()
    if num_photos >= MAX_NUM_PHOTOS:
        return render_to_response('account/max_photos.html', context_instance=RequestContext(request))

    if request.method == 'POST':
        form = UploadPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(request.user, request.FILES['photo'])
            return HttpResponseRedirect(reverse('libravatar.account.views.crop_photo'))
    else:
        form = UploadPhotoForm()

    return render_to_response('account/upload_photo.html', { 'form': form },
                              context_instance=RequestContext(request))

@login_required
def crop_photo(request, photo_id=None):
    if request.method == 'POST':
        photo = Photo.objects.get(id=photo_id)
        if photo.user.id != request.user.id:
            return render_to_response('account/email_notowner.html',
                                      context_instance=RequestContext(request))
        else:
            x = int(request.POST['x'])
            y = int(request.POST['y'])
            w = int(request.POST['w'])
            h = int(request.POST['h'])
            filename = '%s%s' % (settings.AVATAR_ROOT, photo.pathname())
            img = Image.open(filename,'r')
            #TODO: Check that w/h values make sense! >0
            #TODO: set defaults in template too
            cropped = img.crop((x,y,x+w,y+h))
            cropped.load()
            if max(w,h) > 512:
                cropped = cropped.resize((512,512))
            cropped.save(filename)
            return HttpResponseRedirect(reverse('libravatar.account.views.profile'))
    photo = Photo.objects.filter(user=request.user).order_by('id').reverse()[0]

    return render_to_response('account/crop_photo.html', {'photo': photo, 'needs_jquery':True, 'needs_jcrop':True},
                              context_instance=RequestContext(request))
    

@login_required
def delete_photo(request, photo_id):
    try:
        photo = Photo.objects.get(id=photo_id)
    except Photo.DoesNotExist:
        return render_to_response('account/photo_invalid.html', context_instance=RequestContext(request))

    if request.method == 'POST':
        if photo.user.id != request.user.id:
            return render_to_response('account/photo_notowner.html', context_instance=RequestContext(request))
        photo.delete()
        return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

    return render_to_response('account/delete_photo.html', { 'photo': photo },
                              context_instance=RequestContext(request))

@login_required
def assign_photo(request, email_id):
    try:
        email = ConfirmedEmail.objects.get(id=email_id)
    except ConfirmedEmail.DoesNotExist:
        return render_to_response('account/email_invalid.html',
                                  context_instance=RequestContext(request))

    if email.user.id != request.user.id:
        return render_to_response('account/email_notowner.html',
                                  context_instance=RequestContext(request))

    if request.method == 'POST':
        photo = None
        if 'photo_id' in request.POST and request.POST['photo_id']:
            try:
                photo = Photo.objects.get(id=request.POST['photo_id'])
            except Photo.DoesNotExist:
                return render_to_response('account/photo_invalid.html',
                                          context_instance=RequestContext(request))

        if photo and (photo.user.id != request.user.id):
            return render_to_response('account/photo_notowner.html',
                                      context_instance=RequestContext(request))

        email.set_photo(photo)
        return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

    photos = Photo.objects.filter(user=request.user)
    return render_to_response('account/assign_photo.html', {'photos': photos, 'email': email},
                              context_instance=RequestContext(request))
