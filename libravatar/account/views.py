# Copyright (C) 2011  Francois Marier <francois@libravatar.org>
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

from gearman import libgearman
from hashlib import sha256
import json
from openid import oidutil
from openid.consumer import consumer
from StringIO import StringIO

from django_openid_auth.models import UserOpenID
from django.core.files import File
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect

from libravatar.account.external_photos import identica_photo, gravatar_photo
from libravatar.account.forms import AddEmailForm, AddOpenIdForm, DeleteAccountForm, PasswordResetForm, UploadPhotoForm
from libravatar.account.models import ConfirmedEmail, UnconfirmedEmail, ConfirmedOpenId, UnconfirmedOpenId, DjangoOpenIDStore, Photo, password_reset_key
from libravatar import settings

@csrf_protect
def new(request):
    if settings.DISABLE_SIGNUP:
        return HttpResponseRedirect(settings.LOGIN_URL)
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()

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

    if not request.user.is_anonymous():
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

        photos_to_import = False # are there photos to import at all?
        photos_imported = False

        if 'photo_Identica' in request.POST:
            photos_to_import = True
            p = Photo()
            p.user = user
            p.ip_address = request.META['REMOTE_ADDR']
            if p.import_image('Identica', email.email):
                photos_imported = True

        if 'photo_Gravatar' in request.POST:
            photos_to_import = True
            p = Photo()
            p.user = user
            p.ip_address = request.META['REMOTE_ADDR']
            if p.import_image('Gravatar', email.email):
                photos_imported = True

        if photos_imported:
            return render_to_response('account/photos_imported.html',
                                      context_instance=RequestContext(request))
        elif photos_to_import:
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

def _confirm_claimed_openid(user, remote_address):
    openids = UserOpenID.objects.filter(user=user)
    if 0 == openids.count():
        return # not using OpenID auth
    elif openids.count() > 1:
        return # user has already confirmed lots of OpenIDs

    claimed_id = openids[0].claimed_id
    if ConfirmedOpenId.objects.filter(openid=claimed_id).exists():
        return # already confirmed (by this user or someone else)

    # confirm the claimed ID for the logged in user
    confirmed = ConfirmedOpenId()
    confirmed.user = user
    confirmed.ip_address = remote_address
    confirmed.openid = claimed_id
    confirmed.save()

@csrf_protect
@login_required
def profile(request):
    u = request.user
    _confirm_claimed_openid(u, request.META['REMOTE_ADDR'])

    confirmed_emails = u.confirmed_emails.order_by('email')
    unconfirmed_emails = u.unconfirmed_emails.order_by('email')
    confirmed_openids = u.confirmed_openids.order_by('openid')
    unconfirmed_openids = u.unconfirmed_openids.order_by('openid')
    photos = u.photos.order_by('add_date')
    max_photos = len(photos) >= settings.MAX_NUM_PHOTOS
    max_emails = len(unconfirmed_emails) >= settings.MAX_NUM_UNCONFIRMED_EMAILS

    # force evaluation of the QuerySet objects
    list(confirmed_emails)
    list(unconfirmed_emails)
    list(confirmed_openids)
    list(unconfirmed_openids)
    list(photos)

    return render_to_response('account/profile.html',
                              {'confirmed_emails' : confirmed_emails, 'unconfirmed_emails': unconfirmed_emails,
                               'confirmed_openids' : confirmed_openids, 'unconfirmed_openids': unconfirmed_openids,
                               'photos' : photos, 'max_photos' : max_photos, 'max_emails' : max_emails},
                              context_instance=RequestContext(request))

def openid_logging(message, level=0):
    # Normal messages are not that important
    if (level > 0):
        print message

@csrf_protect
@login_required
def add_openid(request):
    if request.method == 'POST':
        form = AddOpenIdForm(request.POST)
        if form.is_valid():
            openid_id = form.save(request.user)
            if not openid_id:
                return render_to_response('account/openid_notadded.html',
                                          context_instance=RequestContext(request))

            user_url = form.cleaned_data['openid']
            session = {'id': request.session.session_key}

            oidutil.log = openid_logging
            openid_consumer = consumer.Consumer(session, DjangoOpenIDStore())

            try:
                auth_request = openid_consumer.begin(user_url)
            except consumer.DiscoveryFailure, exception:
                return render_to_response('account/openid_discoveryfailure.html', {'message': exception},
                                          context_instance=RequestContext(request))

            if auth_request is None:
                return render_to_response('account/openid_discoveryfailure', {'message': '(unknown error)'},
                                          context_instance=RequestContext(request))

            realm = settings.SITE_URL
            return_url = realm + reverse('libravatar.account.views.confirm_openid', args=[openid_id])

            return HttpResponseRedirect(auth_request.redirectURL(realm, return_url))
    else:
        form = AddOpenIdForm()

    return render_to_response('account/add_openid.html', {'form': form},
                              RequestContext(request))

# CSRF check not needed (OpenID return URL)
@login_required
def confirm_openid(request, openid_id):

    session = {'id': request.session.session_key}
    current_url = settings.SITE_URL + request.path

    oidutil.log = openid_logging
    openid_consumer = consumer.Consumer(session, DjangoOpenIDStore())

    if request.method == 'POST':
        info = openid_consumer.complete(request.POST, current_url)
    else:
        info = openid_consumer.complete(request.GET, current_url)

    if info.status == consumer.FAILURE:
        return render_to_response('account/openid_confirmationfailed.html', {'message': info.message},
                                  context_instance=RequestContext(request))
    elif info.status == consumer.CANCEL:
        return render_to_response('account/openid_confirmationfailed.html', {'message': '(cancelled by user)'},
                                  context_instance=RequestContext(request))
    elif info.status != consumer.SUCCESS:
        return render_to_response('account/openid_confirmationfailed.html', {'message': '(unknown verification error)'},
                                  context_instance=RequestContext(request))

    try:
        unconfirmed = UnconfirmedOpenId.objects.get(id=openid_id)
    except UnconfirmedOpenId.DoesNotExist:
        return render_to_response('account/openid_confirmationfailed.html',
                                  {'message': 'ID %s not found in the database.' % openid_id},
                                  context_instance=RequestContext(request))

    # TODO: check for a reasonable expiration time
    confirmed = ConfirmedOpenId()
    confirmed.user = unconfirmed.user
    confirmed.ip_address = request.META['REMOTE_ADDR']
    confirmed.openid = unconfirmed.openid
    confirmed.save()

    unconfirmed.delete()

    # Also allow user to login using this OpenID
    user_openid = UserOpenID()
    user_openid.user = request.user
    user_openid.claimed_id = confirmed.openid
    user_openid.display_id = confirmed.openid
    user_openid.save()

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

@csrf_protect
@login_required
def remove_confirmed_openid(request, openid_id):
    if request.method == 'POST':
        try:
            openid = ConfirmedOpenId.objects.get(id=openid_id, user=request.user)
        except ConfirmedOpenId.DoesNotExist:
            return render_to_response('account/openid_invalid.html',
                                      context_instance=RequestContext(request))

        openid.delete()

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

@csrf_protect
@login_required
def remove_unconfirmed_openid(request, openid_id):
    if request.method == 'POST':
        try:
            openid = UnconfirmedOpenId.objects.get(id=openid_id, user=request.user)
        except UnconfirmedOpenId.DoesNotExist:
            return render_to_response('account/openid_invalid.html',
                                      context_instance=RequestContext(request))

        openid.delete()

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

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
    num_photos = request.user.photos.count()
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

def _assign_photo(request, identifier_type, identifier):
    if request.method == 'POST':
        photo = None
        if 'photo_id' in request.POST and request.POST['photo_id']:
            try:
                photo = Photo.objects.get(id=request.POST['photo_id'], user=request.user)
            except Photo.DoesNotExist:
                return render_to_response('account/photo_invalid.html',
                                          context_instance=RequestContext(request))

        identifier.set_photo(photo)
        return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

    photos = request.user.photos.order_by('add_date')
    list(photos) # force evaluation of the QuerySet
    return render_to_response('account/assign_photo_%s.html' % identifier_type, {'photos': photos, identifier_type: identifier},
                              context_instance=RequestContext(request))

@csrf_protect
@login_required
def assign_photo_email(request, email_id):
    try:
        email = ConfirmedEmail.objects.get(id=email_id, user=request.user)
    except ConfirmedEmail.DoesNotExist:
        return render_to_response('account/email_invalid.html',
                                  context_instance=RequestContext(request))

    return _assign_photo(request, 'email', email)

@csrf_protect
@login_required
def assign_photo_openid(request, openid_id):
    try:
        openid = ConfirmedOpenId.objects.get(id=openid_id, user=request.user)
    except ConfirmedOpenId.DoesNotExist:
        return render_to_response('account/openid_invalid.html',
                                  context_instance=RequestContext(request))

    return _assign_photo(request, 'openid', openid)

@csrf_protect
def password_reset(request):
    if settings.DISABLE_SIGNUP:
        return HttpResponseRedirect(settings.LOGIN_URL)
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save()
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

@csrf_protect
@login_required
def delete(request):
    if request.method == 'POST':
        form = DeleteAccountForm(request.user, request.POST)
        if form.is_valid():
            username = request.user.username
            download_url = _perform_export(request.user, True)
            Photo.objects.delete_user_photos(request.user)
            request.user.delete() # cascading through unconfirmed and confirmed emails/openids
            logout(request)
            return render_to_response('account/delete_done.html',
                                      {'download_url': download_url, 'username': username},
                                      context_instance=RequestContext(request))
    else:
        form = DeleteAccountForm(request.user)

    uses_openid = UserOpenID.objects.filter(user=request.user).exists()
    return render_to_response('account/delete.html', {'form' : form, 'uses_openid': uses_openid},
                              context_instance=RequestContext(request))

def _perform_export(user, do_delete):
    file_hash = sha256(user.username + user.password).hexdigest()

    emails = []
    for email in user.confirmed_emails.all():
        emails.append(email.email)

    openids = []
    for openid in user.confirmed_openids.all():
        openids.append(openid.openid)

    photos = []
    for photo in user.photos.all():
        photo_details = (photo.filename, photo.format)
        photos.append(photo_details)

    gm_client = libgearman.Client()
    for server in settings.GEARMAN_SERVERS:
        gm_client.add_server(server)

    workload = {'do_delete': do_delete, 'file_hash': file_hash, 'username': user.username,
                'emails': emails, 'openids': openids, 'photos': photos}
    gm_client.do_background('exportaccount', json.dumps(workload))

    download_url = settings.EXPORT_FILES_URL + file_hash + '.xml.gz'
    return download_url

@csrf_protect
@login_required
def export(request):
    if request.method == 'POST':
        download_url = _perform_export(request.user, False)
        return render_to_response('account/export_done.html', {'delete': delete, 'download_url': download_url},
                                  context_instance=RequestContext(request))

    return render_to_response('account/export.html', context_instance=RequestContext(request))
