# Copyright (C) 2010, 2011, 2012, 2013  Francois Marier <francois@libravatar.org>
# Copyright (C) 2010  Jonathan Harker <jon@jon.geek.nz>
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
import os
from StringIO import StringIO
import urllib

from django_openid_auth.models import UserOpenID
from django.core.files import File
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect, csrf_exempt

from libravatar.account.browserid_auth import verify_assertion
from libravatar.account.forms import AddEmailForm, AddOpenIdForm, DeleteAccountForm, PasswordResetForm, UploadPhotoForm
from libravatar.account.models import ConfirmedEmail, UnconfirmedEmail, ConfirmedOpenId, UnconfirmedOpenId, DjangoOpenIDStore, Photo, password_reset_key
from libravatar import settings


@transaction.commit_on_success
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

    return render_to_response('account/new.html', {'form': form},
                              context_instance=RequestContext(request))


# No transactions: confirmation should always work no matter what
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

    # TODO: check for a reasonable expiration time in unconfirmed email

    # check to see whether this email is already confirmed
    if ConfirmedEmail.objects.filter(email=unconfirmed.email).exists():
        return render_to_response('account/email_alreadyconfirmed.html',
                                  context_instance=RequestContext(request))

    (confirmed_id, external_photos) = ConfirmedEmail.objects.create_confirmed_email(
        unconfirmed.user, request.META['REMOTE_ADDR'], unconfirmed.email,
        not request.user.is_anonymous())

    unconfirmed.delete()

    # if there's a single image in this user's profile, assign it to the new email
    confirmed = ConfirmedEmail.objects.get(id=confirmed_id)
    photos = confirmed.user.photos
    if photos.count() == 1:
        confirmed.set_photo(photos.get())

    return render_to_response('account/email_confirmed.html',
                              {'email_id': confirmed_id, 'photos': external_photos},
                              context_instance=RequestContext(request))


@transaction.commit_on_success
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
            email = ConfirmedEmail.objects.get(id=request.POST['email_id'], user=user)
        except ConfirmedEmail.DoesNotExist:
            return render_to_response('account/photos_notimported.html',
                                      context_instance=RequestContext(request))

        photos_to_import = False  # are there photos to import at all?
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


@transaction.commit_on_success
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
            fp = StringIO(photo_contents)  # file pointer to in-memory string buffer
            image = File(fp)
            p = Photo()
            p.user = request.user
            p.save(image)
            return HttpResponseRedirect(reverse('libravatar.account.views.crop_photo', args=[p.id]))

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))


def _confirm_claimed_openid(user, remote_address):
    if user.password != u'!':
        return  # not using OpenID auth

    openids = UserOpenID.objects.filter(user=user)
    if openids.count() != 1:
        return  # only the first OpenID needs to be confirmed this way

    claimed_id = openids[0].claimed_id
    if ConfirmedOpenId.objects.filter(openid=claimed_id).exists():
        return  # already confirmed (by this user or someone else)

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

    has_password = request.user.password != u'!'
    return render_to_response('account/profile.html',
                              {'confirmed_emails': confirmed_emails, 'unconfirmed_emails': unconfirmed_emails,
                               'confirmed_openids': confirmed_openids, 'unconfirmed_openids': unconfirmed_openids,
                               'photos': photos, 'max_photos': max_photos, 'max_emails': max_emails,
                               'has_password': has_password, 'sender_email': settings.SERVER_EMAIL},
                              context_instance=RequestContext(request))


def openid_logging(message, level=0):
    # Normal messages are not that important
    if (level > 0):
        print message


@transaction.commit_on_success
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

            return render_to_response('account/add_openid_redirection.html', {'unconfirmed_id': openid_id},
                                      context_instance=RequestContext(request))
    else:
        form = AddOpenIdForm()

    return render_to_response('account/add_openid.html', {'form': form},
                              RequestContext(request))


# CSRF check not possible (using a meta redirect)
@login_required
def redirect_openid(request, openid_id):
    try:
        unconfirmed = UnconfirmedOpenId.objects.get(id=openid_id, user=request.user)
    except UnconfirmedOpenId.DoesNotExist:
        return render_to_response('account/openid_confirmationfailed.html',
                                  {'message': 'ID %s not found in the database.' % openid_id},
                                  context_instance=RequestContext(request))

    user_url = unconfirmed.openid
    session = {'id': request.session.session_key}

    oidutil.log = openid_logging
    openid_consumer = consumer.Consumer(session, DjangoOpenIDStore())

    try:
        auth_request = openid_consumer.begin(user_url)
    except consumer.DiscoveryFailure as exception:
        print "OpenID discovery failed (userid=%s) for %s" % (request.user.id, user_url)
        return render_to_response('account/openid_discoveryfailure.html', {'message': exception},
                                  context_instance=RequestContext(request))
    except UnicodeDecodeError as exception:
        print "OpenID discovery failed (userid=%s) for %s" % (request.user.id, user_url)
        return render_to_response('account/openid_discoveryfailure.html', {'message': exception},
                                  context_instance=RequestContext(request))

    if auth_request is None:
        return render_to_response('account/openid_discoveryfailure', {'message': '(unknown error)'},
                                  context_instance=RequestContext(request))

    realm = settings.SITE_URL
    return_url = realm + reverse('libravatar.account.views.confirm_openid', args=[openid_id])

    return HttpResponseRedirect(auth_request.redirectURL(realm, return_url))


# No transactions: confirmation should always work no matter what
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
        unconfirmed = UnconfirmedOpenId.objects.get(id=openid_id, user=request.user)
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

    # if there's a single image in this user's profile, assign it to the new email
    photos = confirmed.user.photos
    if photos.count() == 1:
        confirmed.set_photo(photos.get())

    # Also allow user to login using this OpenID (if not taken already)
    if not UserOpenID.objects.filter(claimed_id=confirmed.openid).exists():
        user_openid = UserOpenID()
        user_openid.user = request.user
        user_openid.claimed_id = confirmed.openid
        user_openid.display_id = confirmed.openid
        user_openid.save()

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))


@transaction.commit_on_success
@csrf_protect
@login_required
def remove_confirmed_openid(request, openid_id):
    if request.method == 'POST':
        try:
            openid = ConfirmedOpenId.objects.get(id=openid_id, user=request.user)
        except ConfirmedOpenId.DoesNotExist:
            return render_to_response('account/openid_invalid.html',
                                      context_instance=RequestContext(request))

        has_password = request.user.password != u'!'
        if has_password or UserOpenID.objects.filter(user=request.user).count() > 1:
            # remove it from the auth table as well
            UserOpenID.objects.filter(claimed_id=openid.openid).delete()
            openid.delete()
        else:
            return render_to_response('account/openid_cannotdelete.html',
                                      context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))


@transaction.commit_on_success
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


@transaction.commit_on_success
@csrf_protect
@login_required
def add_email(request):
    if request.method == 'POST':
        form = AddEmailForm(request.POST)
        if form.is_valid():
            if not form.save(request.user):
                return render_to_response('account/email_notadded.html',
                                          {'max_emails': settings.MAX_NUM_UNCONFIRMED_EMAILS},
                                          context_instance=RequestContext(request))
            return HttpResponseRedirect(reverse('libravatar.account.views.profile'))
    else:
        form = AddEmailForm()

    return render_to_response('account/add_email.html', {'form': form},
                              RequestContext(request))


@transaction.commit_on_success
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
        if 'browserid_user' in request.session and request.session['browserid_user'] == email.email:
            # Since we are removing the email to which the BrowserID session is tied,
            # we need to convert the session to a non-BrowserID session
            del(request.session['browserid_user'])

    return HttpResponseRedirect(reverse('libravatar.account.views.profile'))


@transaction.commit_on_success
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


@transaction.commit_on_success
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
                return render_to_response('account/photo_toobig.html', {'max_size': settings.MAX_PHOTO_SIZE},
                                          context_instance=RequestContext(request))

            try:
                photo = form.save(request.user, request.META['REMOTE_ADDR'], photo_data)
            except IOError:
                return render_to_response('account/photo_invalidfile.html', context_instance=RequestContext(request))

            if not photo:
                return render_to_response('account/photo_invalidformat.html', context_instance=RequestContext(request))

            # carry optional parameters to the crop page
            params = {}
            if 'embedded' in request.POST:
                params['embedded'] = request.POST['embedded']
            if 'email' in request.POST:
                params['email'] = request.POST['email']
            elif 'openid' in request.POST:
                params['openid'] = request.POST['openid']
            query_string = urllib.urlencode(params)

            crop_url = reverse('libravatar.account.views.crop_photo', args=[photo.id])
            if query_string:
                crop_url += '?' + query_string
            return HttpResponseRedirect(crop_url)
    else:
        form = UploadPhotoForm()

    email = request.GET.get('email')
    openid = request.GET.get('openid')

    return render_to_response('account/upload_photo.html', {'form': form, 'email': email, 'openid': openid,
                                                            'max_file_size': settings.MAX_PHOTO_SIZE},
                              context_instance=RequestContext(request))


def _perform_crop(request, photo, dimensions=None, email=None, openid=None):
    links_to_create = []

    if email or openid:
        # an automatic link was explicitly requested
        md5_hash = sha256_hash = None
        if email:
            (md5_hash, sha256_hash) = email.set_photo(photo, create_links=False)
        else:
            sha256_hash = openid.set_photo(photo, create_links=False)
        links_to_create.append([md5_hash, sha256_hash])

    elif 1 == request.user.photos.count():
        # it's the first photo, use it for all confirmed emails and OpenIDs
        for email in request.user.confirmed_emails.all():
            (md5_hash, sha256_hash) = email.set_photo(photo, create_links=False)
            links_to_create.append([md5_hash, sha256_hash])

        for openid in request.user.confirmed_openids.all():
            sha256_hash = openid.set_photo(photo, create_links=False)
            links_to_create.append([None, sha256_hash])

    photo.crop(dimensions, links_to_create)

    if '1' == request.POST.get('embedded'):
        return HttpResponseRedirect(reverse('libravatar.account.views.profile_embedded'))
    else:
        return HttpResponseRedirect(reverse('libravatar.account.views.profile'))


@csrf_protect
@login_required
def crop_photo(request, photo_id):
    try:
        photo = Photo.objects.get(id=photo_id, user=request.user)
    except Photo.DoesNotExist:
        return render_to_response('account/photo_invalid.html',
                                  context_instance=RequestContext(request))

    photo_file = settings.UPLOADED_FILES_ROOT + photo.full_filename()
    if not os.path.exists(photo_file):
        return render_to_response('account/uploaded_photo_missing.html',
                                  context_instance=RequestContext(request))

    if request.method == 'POST':
        dimensions = {'x': int(request.POST['x']),
                      'y': int(request.POST['y']),
                      'w': int(request.POST['w']),
                      'h': int(request.POST['h'])}

        email = openid = None
        if 'email' in request.POST:
            try:
                email = ConfirmedEmail.objects.get(email=request.POST['email'])
            except ConfirmedEmail.DoesNotExist:
                pass  # ignore the automatic assignment request

        elif 'openid' in request.POST:
            try:
                openid = ConfirmedOpenId.objects.get(openid=request.POST['openid'])
            except ConfirmedOpenId.DoesNotExist:
                pass  # ignore the automatic assignment request

        return _perform_crop(request, photo, dimensions, email, openid)

    email = request.GET.get('email')
    openid = request.GET.get('openid')

    return render_to_response('account/crop_photo.html',
                              {'photo': photo, 'email': email, 'openid': openid},
                              context_instance=RequestContext(request))


@login_required
def auto_crop(request, photo_id):
    try:
        photo = Photo.objects.get(id=photo_id, user=request.user)
    except Photo.DoesNotExist:
        return render_to_response('account/photo_invalid.html',
                                  context_instance=RequestContext(request))

    return _perform_crop(request, photo)


@transaction.commit_on_success
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

    return render_to_response('account/delete_photo.html', {'photo': photo},
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
        if '1' == request.GET.get('embedded'):
            return HttpResponseRedirect(reverse('libravatar.account.views.profile_embedded'))
        else:
            return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

    # carry optional parameters to the upload page
    params = {}
    if 'embedded' in request.GET:
        params['embedded'] = request.GET['embedded']
    if 'email' == identifier_type:
        params['email'] = identifier
    elif 'openid' == identifier_type:
        params['openid'] = identifier
    query_string = urllib.urlencode(params)

    upload_url = reverse('libravatar.account.views.upload_photo')
    if query_string:
        upload_url += '?' + query_string

    photos = request.user.photos.order_by('add_date')
    list(photos)  # force evaluation of the QuerySet
    return render_to_response('account/assign_photo_%s.html' % identifier_type,
                              {'photos': photos, identifier_type: identifier, 'custom_upload_url': upload_url},
                              context_instance=RequestContext(request))


@transaction.commit_on_success
@csrf_protect
@login_required
def assign_photo_email(request, email_id):
    try:
        email = ConfirmedEmail.objects.get(id=email_id, user=request.user)
    except ConfirmedEmail.DoesNotExist:
        return render_to_response('account/email_invalid.html',
                                  context_instance=RequestContext(request))

    return _assign_photo(request, 'email', email)


@transaction.commit_on_success
@csrf_protect
@login_required
def assign_photo_openid(request, openid_id):
    try:
        openid = ConfirmedOpenId.objects.get(id=openid_id, user=request.user)
    except ConfirmedOpenId.DoesNotExist:
        return render_to_response('account/openid_invalid.html',
                                  context_instance=RequestContext(request))

    return _assign_photo(request, 'openid', openid)


@transaction.commit_on_success
@csrf_protect
def password_reset(request):
    if settings.DISABLE_SIGNUP:
        return HttpResponseRedirect(settings.LOGIN_URL)
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save()
            return render_to_response('account/password_reset_submitted.html',
                                      {'form': form, 'support_email': settings.SUPPORT_EMAIL},
                                      context_instance=RequestContext(request))
    else:
        form = PasswordResetForm()

    return render_to_response('account/password_reset.html', {'form': form},
                              context_instance=RequestContext(request))


@transaction.commit_on_success
@csrf_protect
def password_reset_confirm(request):
    if settings.DISABLE_SIGNUP:
        return HttpResponseRedirect(settings.LOGIN_URL)

    verification_key = None
    email_address = None

    if 'verification_key' in request.GET and request.GET['verification_key']:
        verification_key = request.GET['verification_key'].replace(' ', '')

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
    if u'!' == user.password:
        # no password is set, cannot reset it
        return render_to_response('account/reset_invalidparams.html',
                                  context_instance=RequestContext(request))

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

    return render_to_response('account/password_change.html', {'form': form,
                              'verification_key': verification_key, 'email_address': email_address},
                              context_instance=RequestContext(request))


@transaction.commit_on_success
@csrf_protect
@login_required
def delete(request):
    if request.method == 'POST':
        form = DeleteAccountForm(request.user, request.POST)
        if form.is_valid():
            username = request.user.username
            download_url = _perform_export(request.user, True)
            Photo.objects.delete_user_photos(request.user)
            request.user.delete()  # cascading through unconfirmed and confirmed emails/openids
            logout(request)
            return render_to_response('account/delete_done.html',
                                      {'download_url': download_url, 'username': username},
                                      context_instance=RequestContext(request))
    else:
        form = DeleteAccountForm(request.user)

    has_password = request.user.password != u'!'
    return render_to_response('account/delete.html', {'form': form, 'has_password': has_password},
                              context_instance=RequestContext(request))


def _perform_export(user, do_delete):
    file_hash = sha256(user.username + user.password).hexdigest()

    emails = list(user.confirmed_emails.values_list('email', flat=True))
    openids = list(user.confirmed_openids.values_list('openid', flat=True))

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


@transaction.commit_on_success
@csrf_protect
@login_required
def password_set(request):
    has_password = request.user.password != u'!'
    if has_password or settings.DISABLE_SIGNUP:
        return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return render_to_response('account/password_change_done.html',
                                      context_instance=RequestContext(request))
    else:
        form = SetPasswordForm(request.user)

    return render_to_response('account/password_change.html', {'form': form},
                              context_instance=RequestContext(request))


@transaction.commit_on_success
@csrf_exempt
@login_required
def add_browserid(request):
    if not request.method == 'POST' or not 'assertion' in request.POST:
        return render_to_response('account/browserid_noassertion.json', mimetype='application/json',
                                  context_instance=RequestContext(request))

    (email_address, assertion_error) = verify_assertion(request.POST['assertion'], settings.SITE_URL,
                                                        request.is_secure())

    if not email_address:
        sanitised_error = assertion_error
        if sanitised_error:
            sanitised_error = sanitised_error.replace('"', '')
        return render_to_response('account/browserid_invalidassertion.json', {'error': sanitised_error},
                                  mimetype='application/json', context_instance=RequestContext(request))

    # Check whether or not the email is already confirmed by someone
    if ConfirmedEmail.objects.filter(email=email_address).exists():
        if 'browserid_user' in request.session:
            del(request.session['browserid_user'])
        return render_to_response('account/browserid_emailalreadyconfirmed.json', mimetype='application/json',
                                  context_instance=RequestContext(request))

    (unused, unused) = ConfirmedEmail.objects.create_confirmed_email(
        request.user, request.META['REMOTE_ADDR'], email_address, True)
    request.session['browserid_user'] = email_address

    # remove any unconfirmed emails this user might have for this BrowserID
    UnconfirmedEmail.objects.filter(email=email_address, user=request.user).delete()

    return HttpResponse(json.dumps({"success": True, "user": email_address}), mimetype="application/json")


@transaction.commit_on_success
@csrf_exempt
def login_browserid(request):
    if not request.method == 'POST' or not 'assertion' in request.POST:
        return render_to_response('account/browserid_noassertion.json', mimetype='application/json',
                                  context_instance=RequestContext(request))

    user = authenticate(assertion=request.POST['assertion'], host=settings.SITE_URL,
                        https=request.is_secure(), ip_address=request.META['REMOTE_ADDR'],
                        session=request.session)
    if not user:
        return render_to_response('account/browserid_userauthfailed.json', mimetype='application/json',
                                  context_instance=RequestContext(request))

    browserid_user = request.session['browserid_user']  # do not move below login()!
    login(request, user)
    return HttpResponse(json.dumps({"success": True, "user": browserid_user}), mimetype="application/json")


@transaction.commit_on_success
def login_embedded(request):
    if request.user.is_authenticated():
        if 'browserid_user' in request.session:
            return HttpResponseRedirect(reverse('libravatar.account.views.profile_embedded'))
        else:
            logout(request)  # if logged in without browserid, must logout
    return render_to_response('account/login_embedded.html', context_instance=RequestContext(request))


@login_required
def profile_embedded(request):
    if 'browserid_user' not in request.session:
        return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

    # until a photo has been uploaded, redirect to the upload form
    if request.user.photos.count() < 1:
        return HttpResponseRedirect(reverse('libravatar.account.views.upload_photo') + '?embedded=1')

    email_id = None
    photo_url = None
    confirmed_emails = request.user.confirmed_emails.order_by('email')
    for email in confirmed_emails:
        if email.email == request.session['browserid_user']:
            email_id = email.id
            photo_url = email.photo_url()
            break

    if not email_id or not photo_url:
        print "Couldn't find a confirmed email for browserid_user=%s" % request.session['browserid_user']
        return HttpResponseRedirect(reverse('libravatar.account.views.profile'))

    return render_to_response('account/profile_embedded.html', {'email_id': email_id, 'photo_url': photo_url},
                              context_instance=RequestContext(request))
