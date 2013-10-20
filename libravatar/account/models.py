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
#
# This file incorporates work covered by the following copyright and
# permission notice:
#
#     Copyright (c) 2009, Simon Willison
#     All rights reserved.
#
#     Redistribution and use in source and binary forms, with or without
#     modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice, this
#       list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#
#     THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#     AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#     IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#     DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
#     FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#     DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#     SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#     CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#     OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#     OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import base64
import datetime
from gearman import libgearman
import hashlib
import Image
import json
from openid.store import nonce as oidnonce
from openid.store.interface import OpenIDStore
from openid.association import Association as OIDAssociation
from os import urandom, path, rename
import time
from urllib2 import urlopen, HTTPError, URLError
from urlparse import urlsplit, urlunsplit

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from libravatar import settings
from libravatar.account.external_photos import identica_photo, gravatar_photo

MAX_LENGTH_EMAIL = 254  # http://stackoverflow.com/questions/386294
MAX_LENGTH_IPV6 = 45  # http://stackoverflow.com/questions/166132
#MAX_LENGTH_URL = 2048  # http://stackoverflow.com/questions/754547
MAX_LENGTH_URL = 255  # MySQL can't handle more than that (LP: 1018682)


def password_reset_key(user):
    hash_object = hashlib.new('sha256')
    hash_object.update(user.username + user.password)
    return hash_object.hexdigest()


def file_format(image_type):
    if 'JPEG' == image_type:
        return 'jpg'
    elif 'PNG' == image_type:
        return 'png'
    elif 'GIF' == image_type:
        return 'gif'

    print 'Unsupported file format: %s' % image_type
    return None


def change_photo(photo, md5_hash, sha256_hash):
    '''
    Change the photo that the given hashes point to by deleting/creating hard links.
    '''
    photo_hash = None
    photo_format = None
    if photo:
        photo_hash = photo.filename
        photo_format = photo.format

    gm_client = libgearman.Client()
    for server in settings.GEARMAN_SERVERS:
        gm_client.add_server(server)

    workload = {'photo_hash': photo_hash, 'photo_format': photo_format,
                'md5_hash': md5_hash, 'sha256_hash': sha256_hash}
    gm_client.do_background('changephoto', json.dumps(workload))


class PhotoManager(models.Manager):
    def delete_user_photos(self, user):
        for photo in self.filter(user=user):
            photo.delete(delete_file_on_disk=False)


class Photo(models.Model):
    user = models.ForeignKey(User, related_name='photos')
    ip_address = models.CharField(max_length=MAX_LENGTH_IPV6)
    filename = models.CharField(max_length=64)  # sha256 hash is 64 characters
    format = models.CharField(max_length=3)  # file extension (lowercase)
    add_date = models.DateTimeField(default=datetime.datetime.utcnow)
    objects = PhotoManager()

    class Meta:
        verbose_name = _('photo')
        verbose_name_plural = _('photos')

    def __unicode__(self):
        return settings.USER_FILES_URL + self.full_filename()

    def exists(self):
        return path.isfile(settings.USER_FILES_ROOT + self.full_filename())

    def save(self, image, force_insert=False, force_update=False):
        hash_object = hashlib.new('sha256')
        hash_object.update(urandom(1024) + str(self.user.username))
        self.filename = hash_object.hexdigest()

        # Write file to disk
        tmp_filename = settings.UPLOADED_FILES_ROOT + self.filename + '.tmp'
        destination = open(tmp_filename, 'wb+')
        destination.write(image.read())
        destination.close()

        # Use PIL to read the file format
        img = Image.open(tmp_filename)
        self.format = file_format(img.format)
        if not self.format:
            return False
        super(Photo, self).save(force_insert, force_update)

        dest_filename = settings.UPLOADED_FILES_ROOT + self.full_filename()
        rename(tmp_filename, dest_filename)
        return True

    def delete(self, delete_file_on_disk=True):
        # Remove links to this photo
        for email in self.emails.all():
            email.set_photo(None)
        for openid in self.openids.all():
            openid.set_photo(None)

        if delete_file_on_disk:
            # Queue a job for the photo deletion gearman worker
            gm_client = libgearman.Client()
            for server in settings.GEARMAN_SERVERS:
                gm_client.add_server(server)

            workload = {'file_hash': self.filename, 'format': self.format}
            gm_client.do_background('deletephoto', json.dumps(workload))

        super(Photo, self).delete()

    def uploaded_pathname(self):
        return settings.UPLOADED_FILES_URL + self.full_filename()

    def upload_datetime(self):
        return self.add_date.strftime('%Y-%m-%d %H:%M:%S')

    def full_filename(self):
        return self.filename + '.' + self.format

    def import_image(self, service_name, email_address):
        image_url = False

        if 'Identica' == service_name:
            identica = identica_photo(email_address)
            if identica:
                image_url = identica['image_url']
        elif 'Gravatar' == service_name:
            gravatar = gravatar_photo(email_address)
            if gravatar:
                image_url = gravatar['image_url']

        if not image_url:
            return False

        hash_object = hashlib.new('sha256')
        hash_object.update(service_name + email_address)
        self.filename = hash_object.hexdigest()

        tmp_filename = settings.UPLOADED_FILES_ROOT + self.filename + '.tmp'
        try:
            image = urlopen(image_url)
        except HTTPError as e:
            print '%s import failed with an HTTP error: %s' % (service_name, e.code)
            return False
        except URLError as e:
            print '%s import failed: %s' % (service_name, e.reason)
            return False

        # Write file to disk
        destination = open(tmp_filename, 'wb+')
        destination.write(image.read())
        destination.close()

        # Use PIL to read the file format
        img = Image.open(tmp_filename)
        self.format = file_format(img.format)
        if not self.format:
            return False
        super(Photo, self).save()

        dest_filename = settings.UPLOADED_FILES_ROOT + self.full_filename()
        rename(tmp_filename, dest_filename)
        self.crop()

        return True

    def crop(self, dimensions=None, links_to_create=None):
        if path.isfile(settings.USER_FILES_ROOT + self.full_filename()):
            return  # already done, skip

        if not path.isfile(settings.UPLOADED_FILES_ROOT + self.full_filename()):
            return  # source image doesn't exist, can't crop it

        if not links_to_create:
            links_to_create = []

        x = y = w = h = 0
        if dimensions:
            x = dimensions['x']
            y = dimensions['y']
            w = dimensions['w']
            h = dimensions['h']

        # Queue a job for the cropping/resizing gearman worker
        gm_client = libgearman.Client()
        for server in settings.GEARMAN_SERVERS:
            gm_client.add_server(server)

        workload = {'file_hash': self.filename, 'format': self.format,
                    'x': x, 'y': y, 'w': w, 'h': h, 'links': links_to_create}
        gm_client.do_background('cropresize', json.dumps(workload))


class ConfirmedEmailManager(models.Manager):
    # pylint: disable=R0201
    def create_confirmed_email(self, user, ip_address, email_address, is_logged_in):
        confirmed = ConfirmedEmail()
        confirmed.user = user
        confirmed.ip_address = ip_address
        confirmed.email = email_address
        confirmed.save()

        external_photos = []
        if is_logged_in:
            #identica = identica_photo(confirmed.email)
            #if identica:
            #    external_photos.append(identica)
            gravatar = gravatar_photo(confirmed.email)
            if gravatar:
                external_photos.append(gravatar)

        return (confirmed.id, external_photos)


class ConfirmedEmail(models.Model):
    user = models.ForeignKey(User, related_name='confirmed_emails')
    ip_address = models.CharField(max_length=MAX_LENGTH_IPV6)
    email = models.EmailField(unique=True, max_length=MAX_LENGTH_EMAIL)
    photo = models.ForeignKey(Photo, related_name='emails', blank=True, null=True)
    add_date = models.DateTimeField(default=datetime.datetime.utcnow)
    objects = ConfirmedEmailManager()

    class Meta:
        verbose_name = _('confirmed email')
        verbose_name_plural = _('confirmed emails')

    def __unicode__(self):
        return self.email

    def delete(self):
        self.set_photo(None)
        super(ConfirmedEmail, self).delete()

    def photo_url(self):
        if self.photo:
            return self.photo
        return settings.DEFAULT_PHOTO

    def public_hash(self, algorithm):
        if 'md5' == algorithm:
            hash_object = hashlib.new('md5')
        else:
            hash_object = hashlib.new('sha256')
        hash_object.update(self.email.lower())
        return hash_object.hexdigest()

    def public_url(self, https=False, algorithm='sha256'):
        if https:
            return settings.SECURE_AVATAR_URL + self.public_hash(algorithm)
        else:
            return settings.AVATAR_URL + self.public_hash(algorithm)

    def set_photo(self, photo, create_links=True):
        self.photo = photo
        self.save()
        if create_links:
            change_photo(photo, self.public_hash('md5'), self.public_hash('sha256'))
        else:
            return (self.public_hash('md5'), self.public_hash('sha256'))


class UnconfirmedEmail(models.Model):
    user = models.ForeignKey(User, related_name='unconfirmed_emails')
    email = models.EmailField(max_length=MAX_LENGTH_EMAIL)
    verification_key = models.CharField(max_length=64)
    add_date = models.DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        verbose_name = _('unconfirmed email')
        verbose_name_plural = _('unconfirmed emails')

    def __unicode__(self):
        return self.email + ' ' + _('(unconfirmed)')

    def save(self, force_insert=False, force_update=False):
        hash_object = hashlib.new('sha256')
        hash_object.update(urandom(1024) + str(self.user.username))
        key = hash_object.hexdigest()
        self.verification_key = key

        super(UnconfirmedEmail, self).save(force_insert, force_update)


class UnconfirmedOpenId(models.Model):
    user = models.ForeignKey(User, related_name='unconfirmed_openids')
    openid = models.URLField(unique=False, verify_exists=False, max_length=MAX_LENGTH_URL)
    add_date = models.DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        verbose_name = _('unconfirmed OpenID')
        verbose_name_plural = _('unconfirmed OpenIDs')

    def __unicode__(self):
        return self.openid + ' ' + _('(unconfirmed)')


class ConfirmedOpenId(models.Model):
    user = models.ForeignKey(User, related_name='confirmed_openids')
    ip_address = models.CharField(max_length=MAX_LENGTH_IPV6)
    openid = models.URLField(unique=True, verify_exists=False, max_length=MAX_LENGTH_URL)
    photo = models.ForeignKey(Photo, related_name='openids', blank=True, null=True)
    add_date = models.DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        verbose_name = _('confirmed OpenID')
        verbose_name_plural = _('confirmed OpenIDs')

    def __unicode__(self):
        return self.openid

    def delete(self):
        self.set_photo(None)
        super(ConfirmedOpenId, self).delete()

    def photo_url(self):
        if self.photo:
            return self.photo
        return settings.DEFAULT_PHOTO

    def public_hash(self):
        url = urlsplit(self.openid)
        lowercase_value = urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path, url.query, url.fragment))  # pylint: disable=E1103
        hash_object = hashlib.new('sha256')
        hash_object.update(lowercase_value)
        return hash_object.hexdigest()

    def public_url(self, https=False):
        if https:
            return settings.SECURE_AVATAR_URL + self.public_hash()
        else:
            return settings.AVATAR_URL + self.public_hash()

    def set_photo(self, photo, create_links=True):
        self.photo = photo
        self.save()
        if create_links:
            change_photo(photo, None, self.public_hash())
        else:
            return self.public_hash()


# Classes related to the OpenID Store (from https://github.com/simonw/django-openid)

class OpenIDNonce(models.Model):
    server_url = models.CharField(max_length=255)
    timestamp = models.IntegerField()
    salt = models.CharField(max_length=128)

    def __unicode__(self):
        return u"OpenIDNonce: %s for %s" % (self.salt, self.server_url)


class OpenIDAssociation(models.Model):
    server_url = models.TextField(max_length=2047)
    handle = models.CharField(max_length=255)
    secret = models.TextField(max_length=255)  # stored base64 encoded
    issued = models.IntegerField()
    lifetime = models.IntegerField()
    assoc_type = models.TextField(max_length=64)

    def __unicode__(self):
        return u"OpenIDAssociation: %s, %s" % (self.server_url, self.handle)


class DjangoOpenIDStore(OpenIDStore):
    """
    The Python openid library needs an OpenIDStore subclass to persist data
    related to OpenID authentications. This one uses our Django models.
    """

    def storeAssociation(self, server_url, association):
        assoc = OpenIDAssociation(server_url=server_url,
                                  handle=association.handle,
                                  secret=base64.encodestring(association.secret),
                                  issued=association.issued,
                                  lifetime=association.issued,
                                  assoc_type=association.assoc_type)
        assoc.save()

    def getAssociation(self, server_url, handle=None):
        assocs = []
        if handle is not None:
            assocs = OpenIDAssociation.objects.filter(server_url=server_url,
                                                      handle=handle)
        else:
            assocs = OpenIDAssociation.objects.filter(server_url=server_url)
        if not assocs:
            return None
        associations = []
        for assoc in assocs:
            association = OIDAssociation(assoc.handle, base64.decodestring(assoc.secret),
                                         assoc.issued, assoc.lifetime, assoc.assoc_type)
            if association.getExpiresIn() == 0:
                self.removeAssociation(server_url, assoc.handle)
            else:
                associations.append((association.issued, association))
        if not associations:
            return None
        return associations[-1][1]

    def removeAssociation(self, server_url, handle):
        assocs = list(OpenIDAssociation.objects.filter(server_url=server_url,
                                                       handle=handle))
        assocs_exist = len(assocs) > 0
        for assoc in assocs:
            assoc.delete()
        return assocs_exist

    def useNonce(self, server_url, timestamp, salt):
        # Has nonce expired?
        if abs(timestamp - time.time()) > oidnonce.SKEW:
            return False
        try:
            nonce = OpenIDNonce.objects.get(server_url__exact=server_url,
                                            timestamp__exact=timestamp,
                                            salt__exact=salt)
        except OpenIDNonce.DoesNotExist:
            nonce = OpenIDNonce.objects.create(server_url=server_url,
                                               timestamp=timestamp,
                                               salt=salt)
            return True
        nonce.delete()
        return False

    def cleanupNonces(self):
        ts = int(time.time()) - oidnonce.SKEW
        OpenIDNonce.objects.filter(timestamp__lt=ts).delete()

    def cleanupAssociations(self):
        OpenIDAssociation.objects.extra(where=['issued + lifetimeint < (%s)' % time.time()]).delete()

    def getAuthKey(self):
        # Use first AUTH_KEY_LEN characters of md5 hash of SECRET_KEY
        hash_object = hashlib.new('md5')
        hash_object.update(settings.SECRET_KEY)
        return hash_object.hexdigest()[:self.AUTH_KEY_LEN]
