from hashlib import md5, sha1, sha256
from os import link, unlink

from django.db import models
from django.contrib.auth.models import User

from libravatar.settings import MEDIA_URL, MEDIA_ROOT, DEFAULT_PHOTO

class Photo(models.Model):
    user = models.ForeignKey(User)
    filename = models.CharField(max_length=64) # sha256 hash is 64 characters
    format = models.CharField(max_length=3) # png or jpg
    add_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return MEDIA_URL + self.pathname()

    def pathname(self):
        return 'uploaded/' + self.filename + '.' + self.format

    # TODO: create a method for having photos save themselves to disk (multiple sizes?)

    # TODO: add a delete method which deletes the file from disk and unsets photo from all confirmed emails using it

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
        return MEDIA_URL + DEFAULT_PHOTO

    def public_hash(self, algorithm):
        if 'md5' == algorithm:
            return md5(self.email.lower()).hexdigest()
        elif 'sha1' == algorithm:
            return sha1(self.email.lower()).hexdigest()
        else:
            return sha256(self.email.lower()).hexdigest()

    def set_photo(self, photo):
        self.photo = photo

        # TODO: also link the different sizes of images
        # TODO: use git-like hashed directories to avoid too many files in one directory
        md5_filename =  MEDIA_ROOT + self.public_hash('md5')
        sha1_filename =  MEDIA_ROOT + self.public_hash('sha1')
        sha256_filename =  MEDIA_ROOT + self.public_hash('sha256')

        if photo is None:
            try:
                unlink(md5_filename)
                unlink(sha1_filename)
                unlink(sha256_filename)
            except OSError:
                pass # TODO: do something
        else:
            source_filename = MEDIA_ROOT + photo.pathname()
            try:
                link(source_filename, md5_filename)
                link(source_filename, sha1_filename)
                link(source_filename, sha256_filename)
            except:
                pass # TODO: do something

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
