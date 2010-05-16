from hashlib import sha256
from os import urandom

from django import forms
from django.core.mail import send_mail
from django.core.urlresolvers import reverse

from libravatar.account.models import UnconfirmedEmail, Photo
from libravatar.settings import MEDIA_ROOT

class AddEmailForm(forms.Form):
    email = forms.EmailField()

    def save(self, user):
        unconfirmed = UnconfirmedEmail()
        unconfirmed.email = self.cleaned_data['email']
        unconfirmed.user = user

        salted_username = urandom(1024) + str(user.username)
        key = sha256(salted_username).hexdigest()
        unconfirmed.verification_key = key

        unconfirmed.save()

        SITE_URL = 'http://libravatar.org' # TODO: move this to settings.py? or grab the currently running URL?
        link = SITE_URL + reverse('libravatar.account.views.confirm_email') + '?verification_key=' + key

        email_subject = 'Confirm your email address on libravatar.org'
        email_body = """Someone, probably you, requested that this email address be added to their
libravatar account.

If that's what you want, please confirm that you are the owner of this
email address by clicking the following link:

  %(verification_link)s

Otherwise, please accept our apologies and ignore this message.

- The libravatar.org accounts team
""" % {'verification_link' : link }

        send_mail(email_subject, email_body, 'accounts@libravatar.org', [unconfirmed.email])

class UploadPhotoForm(forms.Form):
    photo = forms.ImageField()

    def save(self, user, image):
        format = 'jpg' # TODO: add support for PNG files too
        salted_username = sha256(urandom(1024) + str(user.username)).hexdigest()
        dest_filename = MEDIA_ROOT + 'uploaded/' + salted_username  + '.' + format

        # Write file to disk
        destination = open(dest_filename, 'wb+')
        for chunk in image.chunks():
            destination.write(chunk)
            destination.close()

        # Link this file to the user's profile
        p = Photo()
        p.user = user
        p.filename = salted_username
        p.format = format
        p.save()
