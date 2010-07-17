# Copyright (C) 2010  Francois Marier <francois@libravatar.org>
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

from hashlib import sha256

from django import forms
from django.core.mail import send_mail
from django.core.urlresolvers import reverse

from libravatar import settings
from libravatar.account.models import ConfirmedEmail, UnconfirmedEmail, Photo, password_reset_key

class AddEmailForm(forms.Form):
    email = forms.EmailField()

    def save(self, user):
        unconfirmed = UnconfirmedEmail()
        unconfirmed.email = self.cleaned_data['email']
        unconfirmed.user = user
        unconfirmed.save()

        link = settings.SITE_URL + reverse('libravatar.account.views.confirm_email') + '?verification_key=' + unconfirmed.verification_key

        email_subject = 'Confirm your email address on %s' % settings.SITE_NAME
        email_body = """Someone, probably you, requested that this email address be added to their
%(site_name)s account.

If that's what you want, please confirm that you are the owner of this
email address by clicking the following link:

  %(verification_link)s

Otherwise, please accept our apologies and ignore this message.

- The %(site_name)s accounts team
""" % {'verification_link' : link, 'site_name' : settings.SITE_NAME }

        send_mail(email_subject, email_body, settings.FROM_ADDRESS, [unconfirmed.email])

class UploadPhotoForm(forms.Form):
    photo = forms.ImageField()
    not_porn = forms.BooleanField(required=True)
    can_distribute = forms.BooleanField(required=True)

    def save(self, user, image):
        # Link this file to the user's profile
        p = Photo()
        p.user = user
        p.save(image)

class PasswordResetForm(forms.Form):
    email = forms.EmailField()

    def save(self):
        if not self.cleaned_data['email']:
            return False

        try:
            email = ConfirmedEmail.objects.get(email=self.cleaned_data['email'])
        except ConfirmedEmail.DoesNotExist:
            return False

        email_address = email.email
        key = password_reset_key(email.user)

        link = settings.SITE_URL + reverse('libravatar.account.views.password_reset_confirm')
        link += '?verification_key=%s&email_address=%s' % (key, email_address)

        email_subject = 'Password reset for %s' % settings.SITE_NAME
        email_body = """Someone, probably you, requested a password reset for your
%(site_name)s account.

If that's what you want, please go to the following page:

  %(reset_link)s

Otherwise, please accept our apologies and ignore this message.

- The %(site_name)s accounts team
""" % {'reset_link' : link, 'site_name' : settings.SITE_NAME }

        send_mail(email_subject, email_body, settings.FROM_ADDRESS, [email_address])

        return True
