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

import datetime
from gearman import libgearman
from hashlib import md5, sha1, sha256
import json
import mimetypes
from openid.store import nonce as oidnonce
from openid.store.interface import OpenIDStore
from openid.association import Association as OIDAssociation
from os import urandom, path
import time, base64
from urllib2 import urlopen
from urlparse import urlsplit, urlunsplit

from django.db import models
from django.contrib.auth.models import User

from libravatar import settings
from libravatar.account.external_photos import identica_photo, gravatar_photo

DEFAULT_IMAGE_FORMAT = 'jpg'
MAX_LENGTH_IPV6 = 45 # http://stackoverflow.com/questions/166132
MAX_LENGTH_URL = 2048 # http://stackoverflow.com/questions/754547

def password_reset_key(user):
    return sha256(user.username + user.password).hexdigest()

def mimetype_format(mime_type):
    if 'image/jpeg' == mime_type:
        return 'jpg'
    elif 'image/png' == mime_type:
        return 'png'
    return None

def uploaded_image_format(image):
    '''
    Take an UploadedFile and guess its type (png or jpg)
    '''
    # Check the mimetype sent by the browser
    image_format = mimetype_format(image.content_type)
    if image_format:
        return image_format

    # Fallback on the filename of the uploaded file
    (mime_type, unused) = mimetypes.guess_type(image.name)
    image_format = mimetype_format(mime_type)
    if image_format:
        return image_format

    print "WARN: cannot identify the remote image type: path=%s" % image.name
    return DEFAULT_IMAGE_FORMAT

def remote_image_format(image_url):
    '''
    Take an URL and extract the last part of it (without the
    query_string) and hope that it contains a file extension.
    '''
    (mime_type, unused) = mimetypes.guess_type(image_url)
    image_format = mimetype_format(mime_type)
    if image_format:
        return image_format

    print "WARN: cannot identify the remote image type: url=%s" % image_url
    return DEFAULT_IMAGE_FORMAT

def change_photo(photo, md5_hash, sha1_hash, sha256_hash):
    '''
    Change the photo that the given hashes point to by deleting/creating hard links.
    '''
    photo_filename = None
    if photo:
        photo_filename = photo.full_filename()

    gm_client = libgearman.Client()
    for server in settings.GEARMAN_SERVERS:
        gm_client.add_server(server)

    workload = {'photo_filename': photo_filename, 'md5_hash': md5_hash,
                'sha1_hash': sha1_hash, 'sha256_hash': sha256_hash}
    gm_client.do_background('changephoto', json.dumps(workload))

class PhotoManager(models.Manager):
    def delete_user_photos(self, user):
        for photo in self.filter(user=user):
            photo.delete() # deletes the photo on disk as well

class Photo(models.Model):
    user = models.ForeignKey(User, related_name='photos')
    ip_address = models.CharField(max_length=MAX_LENGTH_IPV6)
    filename = models.CharField(max_length=64) # sha256 hash is 64 characters
    format = models.CharField(max_length=3) # png or jpg
    add_date = models.DateTimeField(default=datetime.datetime.utcnow)
    objects = PhotoManager()

    def __unicode__(self):
        return settings.USER_FILES_URL + self.full_filename()

    def save(self, image, force_insert=False, force_update=False):
        self.format = uploaded_image_format(image)
        self.filename = sha256(urandom(1024) + str(self.user.username)).hexdigest()
        super(Photo, self).save(force_insert, force_update)

        # Write file to disk
        dest_filename = settings.UPLOADED_FILES_ROOT + self.full_filename()
        with open(dest_filename, 'wb+') as destination:
            # FIXME: HACK: temporarily disabling chunks for now - need to be able to write from a non-filesystem file object or find some other way to handle writing to file from a buffer in memory.
            destination.write(image.read())

    def delete(self):
        # Remove links to this photo
        for email in self.emails.all():
            email.set_photo(None)
        for openid in self.openids.all():
            openid.set_photo(None)

        # Queue a job for the photo deletion gearman worker
        gm_client = libgearman.Client()
        for server in settings.GEARMAN_SERVERS:
            gm_client.add_server(server)

        workload = {'filename' : self.full_filename()}
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

        self.format = remote_image_format(image_url)
        self.filename = sha256(service_name + email_address).hexdigest()
        super(Photo, self).save()

        dest_filename = settings.UPLOADED_FILES_ROOT + self.full_filename()
        image = urlopen(image_url)

        # Write file to disk
        destination = open(dest_filename, 'wb+')
        destination.write(image.read())
        destination.close()
        self.crop()

        return True

    def crop(self, x=0, y=0, w=0, h=0):
        if path.isfile(settings.USER_FILES_ROOT + self.full_filename()):
            return # already done, skip

        if not path.isfile(settings.UPLOADED_FILES_ROOT + self.full_filename()):
            return # source image doesn't exist, can't crop it

        # Queue a job for the cropping/resizing gearman worker
        gm_client = libgearman.Client()
        for server in settings.GEARMAN_SERVERS:
            gm_client.add_server(server)

        workload = {'filename' : self.full_filename(),
                    'x' : x, 'y' : y, 'w' : w, 'h' : h}
        gm_client.do_background('cropresize', json.dumps(workload))

class ConfirmedEmail(models.Model):
    user = models.ForeignKey(User, related_name='confirmed_emails')
    ip_address = models.CharField(max_length=MAX_LENGTH_IPV6)
    email = models.EmailField(unique=True)
    photo = models.ForeignKey(Photo, related_name='emails', blank=True, null=True)
    add_date = models.DateTimeField(default=datetime.datetime.utcnow)

    def __unicode__(self):
        return self.email

    def delete(self):
        self.set_photo(None)
        super(ConfirmedEmail, self).delete()

    def photo_url(self):
        if self.photo:
            return self.photo
        return settings.MEDIA_URL + '/img/' + settings.DEFAULT_PHOTO

    def public_hash(self, algorithm):
        if 'md5' == algorithm:
            return md5(self.email.lower()).hexdigest()
        elif 'sha1' == algorithm:
            return sha1(self.email.lower()).hexdigest()
        else:
            return sha256(self.email.lower()).hexdigest()

    def set_photo(self, photo):
        self.photo = photo
        change_photo(photo, self.public_hash('md5'), self.public_hash('sha1'), self.public_hash('sha256'))
        self.save()

class UnconfirmedEmail(models.Model):
    user = models.ForeignKey(User, related_name='unconfirmed_emails')
    email = models.EmailField()
    verification_key = models.CharField(max_length=64)
    add_date = models.DateTimeField(default=datetime.datetime.utcnow)

    def __unicode__(self):
        return self.email + ' (unconfirmed)'

    def save(self, force_insert=False, force_update=False):
        salted_username = urandom(1024) + str(self.user.username)
        key = sha256(salted_username).hexdigest()
        self.verification_key = key

        super(UnconfirmedEmail, self).save(force_insert, force_update)

class UnconfirmedOpenId(models.Model):
    user = models.ForeignKey(User, related_name='unconfirmed_openids')
    openid = models.URLField(unique=True, verify_exists=False, max_length=MAX_LENGTH_URL)
    add_date = models.DateTimeField(default=datetime.datetime.utcnow)

    def __unicode__(self):
        return self.openid + ' (unconfirmed)'

class ConfirmedOpenId(models.Model):
    user = models.ForeignKey(User, related_name='confirmed_openids')
    ip_address = models.CharField(max_length=MAX_LENGTH_IPV6)
    openid = models.URLField(unique=True, verify_exists=False, max_length=MAX_LENGTH_URL)
    photo = models.ForeignKey(Photo, related_name='openids', blank=True, null=True)
    add_date = models.DateTimeField(default=datetime.datetime.utcnow)

    def __unicode__(self):
        return self.openid

    def delete(self):
        self.set_photo(None)
        super(ConfirmedOpenId, self).delete()

    def photo_url(self):
        if self.photo:
            return self.photo
        return settings.MEDIA_URL + '/img/' + settings.DEFAULT_PHOTO

    def public_hash(self, algorithm):
        url = urlsplit(self.openid)
        lowercase_value = urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path, url.query, url.fragment)) # pylint: disable=E1103

        if 'md5' == algorithm:
            return md5(lowercase_value).hexdigest()
        elif 'sha1' == algorithm:
            return sha1(lowercase_value).hexdigest()
        else:
            return sha256(lowercase_value).hexdigest()

    def set_photo(self, photo):
        self.photo = photo
        change_photo(photo, self.public_hash('md5'), self.public_hash('sha1'), self.public_hash('sha256'))
        self.save()

# Classes related to the OpenID Store (from https://github.com/simonw/django-openid)

class OpenIDNonce(models.Model):
    server_url = models.CharField(max_length=255)
    timestamp = models.IntegerField()
    salt = models.CharField(max_length=40)
    
    def __unicode__(self):
        return u"OpenIDNonce: %s for %s" % (self.salt, self.server_url)

class OpenIDAssociation(models.Model):
    server_url = models.TextField(max_length=2047)
    handle = models.CharField(max_length=255)
    secret = models.TextField(max_length=255) # Stored base64 encoded
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
        assoc = OpenIDAssociation(
            server_url = server_url,
            handle = association.handle,
            secret = base64.encodestring(association.secret),
            issued = association.issued,
            lifetime = association.issued,
            assoc_type = association.assoc_type
        )
        assoc.save()
    
    def getAssociation(self, server_url, handle=None):
        assocs = []
        if handle is not None:
            assocs = OpenIDAssociation.objects.filter(
                server_url = server_url, handle = handle
            )
        else:
            assocs = OpenIDAssociation.objects.filter(
                server_url = server_url
            )
        if not assocs:
            return None
        associations = []
        for assoc in assocs:
            association = OIDAssociation(
                assoc.handle, base64.decodestring(assoc.secret), assoc.issued,
                assoc.lifetime, assoc.assoc_type
            )
            if association.getExpiresIn() == 0:
                self.removeAssociation(server_url, assoc.handle)
            else:
                associations.append((association.issued, association))
        if not associations:
            return None
        return associations[-1][1]
    
    def removeAssociation(self, server_url, handle):
        assocs = list(OpenIDAssociation.objects.filter(
            server_url = server_url, handle = handle
        ))
        assocs_exist = len(assocs) > 0
        for assoc in assocs:
            assoc.delete()
        return assocs_exist
    
    def useNonce(self, server_url, timestamp, salt):
        # Has nonce expired?
        if abs(timestamp - time.time()) > oidnonce.SKEW:
            return False
        try:
            nonce = OpenIDNonce.objects.get(
                server_url__exact = server_url,
                timestamp__exact = timestamp,
                salt__exact = salt
            )
        except OpenIDNonce.DoesNotExist:
            nonce = OpenIDNonce.objects.create(
                server_url = server_url,
                timestamp = timestamp,
                salt = salt
            )
            return True
        nonce.delete()
        return False
    
    def cleanupNonces(self):
        OpenIDNonce.objects.filter(
            timestamp__lt = (int(time.time()) - oidnonce.SKEW)
        ).delete()
    
    def cleanupAssociations(self):
        OpenIDAssociation.objects.extra(
            where=['issued + lifetimeint < (%s)' % time.time()]
        ).delete()
    
    def getAuthKey(self):
        # Use first AUTH_KEY_LEN characters of md5 hash of SECRET_KEY
        return md5(settings.SECRET_KEY).hexdigest()[:self.AUTH_KEY_LEN]
