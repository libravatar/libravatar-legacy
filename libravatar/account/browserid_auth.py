# Copyright (C) 2011  Francois Marier <francois@libravatar.org>
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
from urllib2 import urlopen, HTTPError, URLError
import time

from django.contrib.auth.models import User
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from libravatar import settings
from libravatar.account.models import ConfirmedEmail

URL_TIMEOUT = 5 # in seconds

# TODO: use request.get_host() instead of settings.SITE_URL
def _browserid_audience(site_url):
    site_url = site_url.lower()

    if 0 == site_url.find('https://'):
        return site_url[8:]
    elif 0 == site_url.find('http://'):
        return site_url[7:]
    else:
        print 'Invalid SITE_URL setting: %s' % site_url
        return None

def verify_assertion(assertion):
    if not assertion:
        return (None, None)

    audience = _browserid_audience(settings.SITE_URL)
    verification_data = 'assertion=%s&audience=%s' % (assertion, audience)

    fh = None
    try:
        # TODO: verify SSL certs
        fh = urlopen('https://browserid.org/verify', data=verification_data, timeout=URL_TIMEOUT)
    except HTTPError as e:
        print 'BrowserID verification service return a %s HTTP error' % e.code
    except URLError as e:
        print 'BrowserID verification service failure: %s' % e.reason

    if not fh:
        return (None, None)

    verification_response = fh.read()
    try:
        parsed_response = json.loads(verification_response)
    except ValueError:
        parsed_response = None

    if not parsed_response:
        print 'BrowserID verification service returned non-JSON or empty output: %s' % verification_response
        return (None, None)

    if 'status' not in parsed_response:
        print 'BrowserID verification service did not return a status code'
        return (None, None)
    if 'failure' == parsed_response['status']:
        return (None, parsed_response['reason'])
    if parsed_response['status'] != 'okay':
        return (None, _('unexpected "%s" status code' % parsed_response['status']))

    if 'audience' not in parsed_response:
        print 'BrowserID verification service did not return a status code'
        return (None, None)
    if parsed_response['audience'] != _browserid_audience(settings.SITE_URL):
        return (None, _('assertion only valid for an audience of "%s"' % parsed_response['audience']))

    if 'valid-until' not in parsed_response:
        print 'BrowserID verification service did not return an expiration'
        return (None, None)
    if parsed_response['valid-until'] < time.time():
        expiration = time.gmtime(parsed_response['valid-until'] / 1000)
        formatted_expiration = time.strftime('%Y-%m-%dT%H:%M:%S', expiration)
        return (None, _('assertion expired on %s' % formatted_expiration))

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

    def authenticate(self, assertion=None):
        (email_address, unused) = verify_assertion(assertion)

        if not email_address:
            return None

        # Find user account that contains this email address
        try:
            confirmed_email = ConfirmedEmail.objects.get(email=email_address)
        except ConfirmedEmail.DoesNotExist:
            return None # TODO: add support for account creation

        return confirmed_email.user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
