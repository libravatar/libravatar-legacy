# Copyright (C) 2010  Francois Marier <francois@libravatar.org>
#                     Jonathan Harker <jon@jon.geek.nz>
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

from hashlib import md5, sha1, sha256
from os import link, unlink, urandom, path
from urllib2 import urlopen

from django.db import models
from django.contrib.auth.models import User

from libravatar import settings
from libravatar.account.external_photos import *
from libravatar.avatar.image import resized_avatar

def delete_if_exists(filename):
    if path.isfile(filename):
        unlink(filename)

def password_reset_key(user):
    return sha256(user.username + user.password).hexdigest()

class Photo(models.Model):
    user = models.ForeignKey(User)
    filename = models.CharField(max_length=64) # sha256 hash is 64 characters
    format = models.CharField(max_length=3) # png or jpg
    add_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return settings.AVATAR_URL + self.pathname()

    def pathname(self):
        return 'uploaded/' + self.filename + '.' + self.format

    def save(self, image, force_insert=False, force_update=False):
        self.format = 'jpg' # TODO: add support for PNG files too
        self.filename = sha256(urandom(1024) + str(self.user.username)).hexdigest()
        super(Photo, self).save(force_insert, force_update)

        # Write file to disk
        dest_filename = settings.AVATAR_ROOT + self.pathname()
        with open(dest_filename, 'wb+') as destination:
            # TODO: HACK: temporarily disabling chunks for now - need to be able to write from a non-filesystem file object or find some other way to handle writing to file from a buffer in memory.
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

        self.format = 'jpg' # TODO: add support for PNG files too
        self.filename = sha256(service_name + email_address).hexdigest()
        super(Photo, self).save()

        dest_filename = settings.AVATAR_ROOT + self.pathname()
        image = urlopen(image_url)

        # Write file to disk
        destination = open(dest_filename, 'wb+')
        destination.write(image.read())
        destination.close()

        return True

    def delete(self):
        # Remove links to this photo
        for email in ConfirmedEmail.objects.filter(photo=self):
            email.set_photo(None)

        delete_if_exists(settings.AVATAR_ROOT + self.pathname())
        super(Photo, self).delete()

class ConfirmedEmail(models.Model):
    user = models.ForeignKey(User)
    email = models.EmailField(unique=True)
    photo = models.ForeignKey(Photo, blank=True, null=True)
    add_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.email

    def photo_url(self):
        if self.photo:
            return self.photo
        return settings.MEDIA_URL + 'img/' + settings.DEFAULT_PHOTO

    def public_hash(self, algorithm):
        if 'md5' == algorithm:
            return md5(self.email.lower()).hexdigest()
        elif 'sha1' == algorithm:
            return sha1(self.email.lower()).hexdigest()
        else:
            return sha256(self.email.lower()).hexdigest()

    def set_photo(self, photo):
        self.photo = photo

        # TODO: use git-like hashed directories to avoid too many files in one directory
        md5_filename = settings.AVATAR_ROOT + self.public_hash('md5')
        sha1_filename = settings.AVATAR_ROOT + self.public_hash('sha1')
        sha256_filename = settings.AVATAR_ROOT + self.public_hash('sha256')

        # Remove old image
        delete_if_exists(md5_filename)
        delete_if_exists(sha1_filename)
        delete_if_exists(sha256_filename)

        # Delete all resized images
        for size in xrange(settings.AVATAR_MIN_SIZE, settings.AVATAR_MAX_SIZE):
            size_dir = settings.AVATAR_ROOT + '/%s/' % size
            delete_if_exists(size_dir + self.public_hash('md5'))
            delete_if_exists(size_dir + self.public_hash('sha1'))
            delete_if_exists(size_dir + self.public_hash('sha256'))

        if photo is not None:
            source_filename = settings.AVATAR_ROOT + photo.pathname()
            link(source_filename, md5_filename)
            link(source_filename, sha1_filename)
            link(source_filename, sha256_filename)

            # Generate resized images for common sizes
            for size in settings.AVATAR_PREGENERATED_SIZES:
                resized_filename = resized_avatar(self.public_hash('md5'), size)
                
                # TODO: these should go once it's automatically done in image.py
                output_dir = settings.AVATAR_ROOT + '/%s/' % size
                link(resized_filename, output_dir + self.public_hash('sha1'))
                link(resized_filename, output_dir + self.public_hash('sha256'))

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
