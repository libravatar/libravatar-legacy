# Copyright (C) 2010, 2011  Francois Marier <francois@libravatar.org>
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

import urllib
from urlparse import urlsplit, urlunsplit

from django import forms
from django.core.mail import send_mail
from django.core.urlresolvers import reverse

from libravatar import settings
from libravatar.account.models import ConfirmedEmail, UnconfirmedEmail, ConfirmedOpenId, UnconfirmedOpenId, Photo, password_reset_key, MAX_LENGTH_URL

MIN_LENGTH_URL = 5 # completely arbitrary guess

class AddEmailForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        """
        Enforce domain restriction and lowercase email
        """
        data = self.cleaned_data['email'].lower()
        domain = settings.REQUIRED_DOMAIN.lower()

        if domain and "@%s" % domain not in data:
            raise forms.ValidationError("Valid email addresses end with @%s" % domain)

        return data

    def save(self, user):
        # Enforce the maximum number of unconfirmed emails a user can have
        num_unconfirmed = user.unconfirmed_emails.count()
        if num_unconfirmed >= settings.MAX_NUM_UNCONFIRMED_EMAILS:
            return False

        # Check whether or not a confirmation email has been sent by this user already
        if UnconfirmedEmail.objects.filter(user=user, email=self.cleaned_data['email']).exists():
            return False

        # Check whether or not the email is already confirmed by someone
        if ConfirmedEmail.objects.filter(email=self.cleaned_data['email']).exists():
            return False

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

        send_mail(email_subject, email_body, settings.SERVER_EMAIL, [unconfirmed.email])
        return True

class AddOpenIdForm(forms.Form):
    openid = forms.URLField(verify_exists=False, min_length=MIN_LENGTH_URL, max_length=MAX_LENGTH_URL, initial='http://', label='OpenID')

    def clean_openid(self):
        """
        Enforce domain restriction
        """

        # Lowercase the hostname part of the URL
        url = urlsplit(self.cleaned_data['openid'])
        data = urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path, url.query, url.fragment)) # pylint: disable=E1103

        domain = settings.REQUIRED_DOMAIN.lower()

        if domain and "%s/" % domain not in data: # FIXME: improve this check, it's not all that great
            raise forms.ValidationError("Valid OpenID URLs are on this domain: %s" % domain)

        return data

    def save(self, user):
        # Check whether or not the openid is already confirmed by someone
        if ConfirmedOpenId.objects.filter(openid=self.cleaned_data['openid']).exists():
            return False

        unconfirmed = UnconfirmedOpenId()
        unconfirmed.openid = self.cleaned_data['openid']
        unconfirmed.user = user
        try:
            unconfirmed.save()
        except:
            # probably a duplicate URL (e.g. http://localhost and http://localhost/)
            return False

        return unconfirmed.id

class UploadPhotoForm(forms.Form):
    photo = forms.ImageField()
    not_porn = forms.BooleanField(required=True, label='suitable for all ages (i.e. no offensive content)')
    can_distribute = forms.BooleanField(required=True, label='can be freely copied')

    # pylint: disable=R0201
    def save(self, user, ip_address, image):
        # Link this file to the user's profile
        p = Photo()
        p.user = user
        p.ip_address = ip_address
        p.save(image)
        return p

class PasswordResetForm(forms.Form):
    email = forms.EmailField(label="Email address")

    def save(self):
        if not self.cleaned_data['email']:
            return False

        try:
            email = ConfirmedEmail.objects.get(email=self.cleaned_data['email'])
        except ConfirmedEmail.DoesNotExist:
            return False

        email_address = self.cleaned_data['email']
        key = password_reset_key(email.user)

        link = settings.SITE_URL + reverse('libravatar.account.views.password_reset_confirm')
        link += '?verification_key=%s&email_address=%s' % (key, urllib.quote_plus(email_address))

        email_subject = 'Password reset for %s' % settings.SITE_NAME
        email_body = """Someone, probably you, requested a password reset for your
%(site_name)s account.

If that's what you want, please go to the following page:

  %(reset_link)s

Otherwise, please accept our apologies and ignore this message.

- The %(site_name)s accounts team
""" % {'reset_link' : link, 'site_name' : settings.SITE_NAME }

        send_mail(email_subject, email_body, settings.SERVER_EMAIL, [email_address])

        return True

class DeleteAccountForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(render_value=False))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(DeleteAccountForm, self).__init__(*args, **kwargs)

    def clean_password(self):
        data = self.cleaned_data['password']

        if not self.user.check_password(data):
            raise forms.ValidationError('Invalid password')

        return data
