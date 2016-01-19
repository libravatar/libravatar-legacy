# Copyright (C) 2011, 2016  Francois Marier <francois@libravatar.org>
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

# pylint: disable=bad-continuation,invalid-name
import re

from django.test import TestCase
from django.test.client import Client

from views import lookup_ip_address  # pylint: disable=W0403


def match_regexp(result, regexp):
    return re.match(regexp, result)


class ToolsTestCase(TestCase):
    def setUp(self):
        pass  # Nothing to do

    def testIpLookup(self):
        self.assertTrue(match_regexp(lookup_ip_address('www.google.com', False), r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'))
        self.assertTrue(match_regexp(lookup_ip_address('ipv6.google.com', True), r'^[0-9a-f:]+$'))

    def testFullEmailLookup(self):
        c = Client()
        response = c.post('/tools/check/', {'email': 'person@example.com', 'size': '80'})
        self.assertEquals(response.status_code, 200)
        self.assertTrue('MD5 hash: <tt>7de8517bce4457e8390aa4006a1880fb' in response.content)
        self.assertTrue('SHA256 hash: <tt>542d240129883c019e106e3b1b2d3f3cb3537c43c425364de8e951d5a3083345' in response.content)

        response = c.post('/tools/check/', {'email': 'Person@EXAMPLE.com', 'size': '512'})
        self.assertEquals(response.status_code, 200)
        self.assertTrue('MD5 hash: <tt>7de8517bce4457e8390aa4006a1880fb' in response.content)
        self.assertTrue('SHA256 hash: <tt>542d240129883c019e106e3b1b2d3f3cb3537c43c425364de8e951d5a3083345' in response.content)

    def testFullOpenIDLookup(self):
        c = Client()
        response = c.post('/tools/check/', {'openid': 'http://example.com/id/Bob', 'size': '80'})
        self.assertEquals(response.status_code, 200)
        self.assertTrue('SHA256 hash: <tt>80cd0679bb52beac4d5d388c163016dbc5d3f30c262a4f539564236ca9d49ccd' in response.content)

        response = c.post('/tools/check/', {'openid': 'http://EXAMPLE.com/id/Bob', 'size': '80'})
        self.assertEquals(response.status_code, 200)
        self.assertTrue('SHA256 hash: <tt>80cd0679bb52beac4d5d388c163016dbc5d3f30c262a4f539564236ca9d49ccd' in response.content)

    def testErrorMessages(self):
        c = Client()
        response = c.post('/tools/check/', {'email': 'person@example.com', 'openid': 'http://example.com/id/Bob', 'size': '80'})
        self.assertTrue('You cannot provide both an email and an OpenID' in response.content)

        response = c.post('/tools/check/', {'email': 'personexample.com', 'size': '80'})
        self.assertTrue('Enter a valid email address' in response.content)

        response = c.post('/tools/check/', {'openid': 'example', 'size': '80'})
        self.assertTrue('Enter a valid URL' in response.content)

        response = c.post('/tools/check/', {'openid': 'example.com', 'size': '520'})
        self.assertTrue('Ensure this value is less than or equal to 512' in response.content)

    def testDomainLookup(self):
        c = Client()
        response = c.post('/tools/check_domain/', {'domain': 'example.com'})
        self.assertEquals(response.status_code, 200)
        self.assertTrue('use <tt>http://cdn.libravatar.org' in response.content)
        self.assertTrue('use <tt>https://seccdn.libravatar.org' in response.content)

        response = c.post('/tools/check_domain/', {'domain': 'fmarier.org'})
        self.assertEquals(response.status_code, 200)
        self.assertTrue('<tt>fmarier.org' in response.content)
        self.assertFalse('use <tt>https://seccdn.libravatar.org' in response.content)

        response = c.post('/tools/check_domain/', {'domain': ''})
        self.assertTrue('This field is required' in response.content)
