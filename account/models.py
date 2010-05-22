from django.db import models
from django.contrib.auth.models import User

from libravatar.settings import MEDIA_URL, DEFAULT_PHOTO

class Photo(models.Model):
    user = models.ForeignKey(User)
    filename = models.CharField(max_length=70) # sha256 hash is 64 characters
    format = models.CharField(max_length=3) # png or jpg
    add_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return MEDIA_URL + 'uploaded/' + self.filename + '.' + self.format

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
        

class UnconfirmedEmail(models.Model):
    user = models.ForeignKey(User)
    email = models.EmailField()
    verification_key = models.CharField(max_length=64)
    add_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.email + ' (unconfirmed)'
