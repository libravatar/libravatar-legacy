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
from hashlib import md5, sha1, sha256
import json
import mimetypes
from os import link, unlink, urandom, path
from urllib2 import urlopen

from django.db import models
from django.contrib.auth.models import User

from libravatar import settings
from libravatar.account.external_photos import identica_photo, gravatar_photo
from libravatar.public.views import resized_avatar

DEFAULT_IMAGE_FORMAT = 'jpg'
MAX_LENGTH_IPV6 = 45 # http://stackoverflow.com/questions/166132
MAX_LENGTH_URL = 2048 # http://stackoverflow.com/questions/754547

def delete_if_exists(filename):
    if path.isfile(filename):
        unlink(filename)

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

def change_photo(identifier, photo, md5_hash, sha1_hash, sha256_hash):
    '''
    Change the photo that the given hashes point to by deleting/creating hard links.
    '''
    # TODO: use git-like hashed directories to avoid too many files in one directory
    md5_filename = settings.AVATAR_ROOT + md5_hash
    sha1_filename = settings.AVATAR_ROOT + sha1_hash
    sha256_filename = settings.AVATAR_ROOT + sha256_hash

    # Remove old image
    delete_if_exists(md5_filename)
    delete_if_exists(sha1_filename)
    delete_if_exists(sha256_filename)

    # Delete all resized images
    for size in xrange(settings.AVATAR_MIN_SIZE, settings.AVATAR_MAX_SIZE):
        size_dir = settings.AVATAR_ROOT + '/%s/' % size

        delete_if_exists(size_dir + md5_hash)
        delete_if_exists(size_dir + sha1_hash)
        delete_if_exists(size_dir + sha256_hash)

    if not photo:
        return

    source_filename = settings.USER_FILES_ROOT + photo.full_filename()
    if not path.isfile(source_filename):
        # cropped photo doesn't exist, don't change anything
        return

    link(source_filename, md5_filename)
    link(source_filename, sha1_filename)
    link(source_filename, sha256_filename)

    # Generate resized images for common sizes
    for size in settings.AVATAR_PREGENERATED_SIZES:
        (resized_filename, unused) = resized_avatar(md5_hash, size)

        # TODO: these should go once it's automatically done in image.py
        output_dir = settings.AVATAR_ROOT + '/%s/' % size
        link(resized_filename, output_dir + sha1_hash)
        link(resized_filename, output_dir + sha256_hash)

class PhotoManager(models.Manager):
    def delete_user_photos(self, user):
        for photo in self.filter(user=user):
            photo.delete() # deletes the photo on disk as well

class Photo(models.Model):
    user = models.ForeignKey(User)
    ip_address = models.CharField(max_length=MAX_LENGTH_IPV6)
    filename = models.CharField(max_length=64) # sha256 hash is 64 characters
    format = models.CharField(max_length=3) # png or jpg
    add_date = models.DateTimeField(auto_now_add=True)
    objects = PhotoManager()

    def __unicode__(self):
        return settings.USER_FILES_URL + self.full_filename()

    def uploaded_pathname(self):
        return settings.UPLOADED_FILES_URL + self.full_filename()

    def upload_datetime(self):
        return self.add_date.strftime('%Y-%m-%d %H:%M:%S')

    def full_filename(self):
        return self.filename + '.' + self.format

    def save(self, image, force_insert=False, force_update=False):
        self.format = uploaded_image_format(image)
        self.filename = sha256(urandom(1024) + str(self.user.username)).hexdigest()
        super(Photo, self).save(force_insert, force_update)

        # Write file to disk
        dest_filename = settings.UPLOADED_FILES_ROOT + self.full_filename()
        with open(dest_filename, 'wb+') as destination:
            # FIXME: HACK: temporarily disabling chunks for now - need to be able to write from a non-filesystem file object or find some other way to handle writing to file from a buffer in memory.
            destination.write(image.read())

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

    def delete(self):
        # Remove links to this photo
        for email in ConfirmedEmail.objects.filter(photo=self):
            email.set_photo(None)
        for openid in LinkedOpenId.objects.filter(photo=self):
            openid.set_photo(None)

        # Queue a job for the photo deletion gearman worker
        gm_client = libgearman.Client()
        for server in settings.GEARMAN_SERVERS:
            gm_client.add_server(server)

        workload = {'filename' : self.full_filename()}
        gm_client.do_background('deletephoto', json.dumps(workload))

        super(Photo, self).delete()

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
    user = models.ForeignKey(User)
    ip_address = models.CharField(max_length=MAX_LENGTH_IPV6)
    email = models.EmailField(unique=True)
    photo = models.ForeignKey(Photo, blank=True, null=True)
    add_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.email

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
        change_photo(self, photo, self.public_hash('md5'), self.public_hash('sha1'), self.public_hash('sha256'))
        self.save()

    def delete(self):
        self.set_photo(None)
        super(ConfirmedEmail, self).delete()

class UnconfirmedEmail(models.Model):
    user = models.ForeignKey(User)
    email = models.EmailField()
    verification_key = models.CharField(max_length=64)
    add_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.email + ' (unconfirmed)'

    def save(self, force_insert=False, force_update=False):
        salted_username = urandom(1024) + str(self.user.username)
        key = sha256(salted_username).hexdigest()
        self.verification_key = key

        super(UnconfirmedEmail, self).save(force_insert, force_update)

class LinkedOpenId(models.Model):
    user = models.ForeignKey(User)
    ip_address = models.CharField(max_length=MAX_LENGTH_IPV6)
    openid = models.URLField(unique=True, verify_exists=False, max_length=MAX_LENGTH_URL)
    photo = models.ForeignKey(Photo, blank=True, null=True)
    add_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.openid

    def photo_url(self):
        if self.photo:
            return self.photo
        return settings.MEDIA_URL + '/img/' + settings.DEFAULT_PHOTO

    def public_hash(self, algorithm):
        # TODO: lowercase the domain part of the OpenID
        if 'md5' == algorithm:
            return md5(self.openid).hexdigest()
        elif 'sha1' == algorithm:
            return sha1(self.openid).hexdigest()
        else:
            return sha256(self.openid).hexdigest()

    def set_photo(self, photo):
        self.photo = photo
        change_photo(self, photo, self.public_hash('md5'), self.public_hash('sha1'), self.public_hash('sha256'))
        self.save()

    def delete(self):
        self.set_photo(None)
        super(LinkedOpenId, self).delete()
