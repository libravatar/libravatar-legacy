# Copyright (C) 2011, 2012  Francois Marier <francois@libravatar.org>
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

import json
import requests

from django.contrib.auth.models import User
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from libravatar import settings
from libravatar.account.models import ConfirmedEmail

URL_TIMEOUT = 5  # in seconds


def _browserid_audience(host, https):
    if https:
        port = 443
    else:
        port = 80

    if ':' in host:
        return host
    else:
        return "%s:%s" % (host, port)


def verify_assertion(assertion, host, https):
    if not assertion:
        return (None, None)

    url = 'https://verifier.login.persona.org/verify'
    audience = _browserid_audience(host, https)
    verification_data = {'assertion': assertion, 'audience': audience}
    headers = {'Content-type': 'application/x-www-form-urlencoded'}

    response = None
    try:
        response = requests.post(url, verify=settings.CACERTS, data=verification_data, headers=headers, timeout=URL_TIMEOUT)
    except requests.exceptions.SSLError:
        print 'Failed to verify the BrowserID TLS certificate'
    except requests.exceptions.ConnectionError:
        print 'Could not connect to the BrowserID verifier'

    if not response or response.status_code != 200:
        return (None, None)

    try:
        parsed_response = json.loads(response.text)
    except ValueError:
        parsed_response = None

    if not parsed_response:
        print 'BrowserID verification service returned non-JSON or empty output: %s' % response.text
        return (None, None)

    if 'status' not in parsed_response:
        print 'BrowserID verification service did not return a status code'
        return (None, None)
    if 'failure' == parsed_response['status']:
        return (None, parsed_response['reason'])
    if parsed_response['status'] != 'okay':
        return (None, _('unexpected "%s" status code' % parsed_response['status']))

    if not 'email' in parsed_response:
        return (None, _('missing email address'))

    email_address = parsed_response['email']
    try:
        validators.validate_email(email_address)
    except ValidationError:
        return (None, _('"%s" is not a valid email address' % email_address))

    return (email_address, None)


# pylint: disable=R0201
class BrowserIDBackend(object):
    supports_anonymous_user = False
    supports_object_permissions = False

    def create_user_from_browserid(self, email_address, ip_address):
        nickname = 'browserid'
        email = ''

        # Pick a username for the user based on their nickname,
        # checking for conflicts.
        i = 1
        while True:
            username = nickname
            if i > 1:
                username += str(i)
            try:
                User.objects.get(username__exact=username)
            except User.DoesNotExist:
                break
            i += 1

        user = User.objects.create_user(username, email, password=None)
        user.is_active = True
        user.save()

        ConfirmedEmail.objects.create_confirmed_email(user, ip_address, email_address, False)
        return user

    def authenticate(self, assertion=None, host=None, https=None, ip_address=None, session=None):
        (email_address, unused) = verify_assertion(assertion, host, https)

        if email_address:
            session['browserid_user'] = email_address
        else:
            return None

        # Find user account that contains this email address
        try:
            confirmed_email = ConfirmedEmail.objects.get(email=email_address)
        except ConfirmedEmail.DoesNotExist:
            confirmed_email = None

        if confirmed_email:
            return confirmed_email.user
        else:
            return self.create_user_from_browserid(email_address, ip_address)

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
