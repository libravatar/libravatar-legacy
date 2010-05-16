from django.db import models
from django.contrib.auth.models import User

class ConfirmedEmail(models.Model):
    user = models.ForeignKey(User)
    email = models.EmailField(unique=True)
    add_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.email

class UnconfirmedEmail(models.Model):
    user = models.ForeignKey(User)
    email = models.EmailField()
    verification_key = models.CharField(max_length=64)
    add_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.email + ' (unconfirmed)'
