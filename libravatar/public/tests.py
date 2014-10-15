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

import random
import unittest

from django.test.client import Client

from views import lookup_avatar_server, mimetype_format, srv_hostname  # pylint: disable=W0403


class PublicTestCase(unittest.TestCase):
    def setUp(self):
        pass  # Nothing to do

    def testMimetypes(self):
        self.assertEquals(mimetype_format('JPEG'), 'image/jpeg')
        self.assertEquals(mimetype_format('PNG'), 'image/png')
        self.assertEquals(mimetype_format('GIF'), 'image/gif')
        self.assertEquals(mimetype_format('BMP'), 'image/jpeg')

    def testDnsLookup(self):
        self.assertEquals(lookup_avatar_server('', False), None)
        self.assertEquals(lookup_avatar_server(None, False), None)
        self.assertEquals(lookup_avatar_server('invalid', True), None)
        self.assertEquals(lookup_avatar_server('example.com', False), None)
        self.assertEquals(lookup_avatar_server('example.com', True), None)
        self.assertEquals(lookup_avatar_server('fmarier.org', False), 'fmarier.org')
        self.assertEquals(lookup_avatar_server('fmarier.org', True), 'fmarier.org')

    def testSrvHostname(self):
        self.assertEquals(srv_hostname([]), (None, None))
        self.assertEquals(srv_hostname([{'target': 'avatars.example.com', 'priority': 0, 'weight': 0, 'port': 80}]),
                          ('avatars.example.com', 80))
        self.assertEquals(srv_hostname([
                          {'target': 'avatars2.example.com', 'priority': 10, 'weight': 0, 'port': 81},
                          {'target': 'avatars.example.com', 'priority': 0, 'weight': 0, 'port': 80},
                          ]),
                          ('avatars.example.com', 80))
        self.assertEquals(srv_hostname([
                          {'target': 'avatars4.example.com', 'priority': 10, 'weight': 0, 'port': 83},
                          {'target': 'avatars3.example.com', 'priority': 10, 'weight': 0, 'port': 82},
                          {'target': 'avatars21.example.com', 'priority': 1, 'weight': 0, 'port': 81},
                          {'target': 'avatars.example.com', 'priority': 10, 'weight': 0, 'port': 80},
                          ]),
                          ('avatars21.example.com', 81))

        # The following ones are randomly selected which is why we
        # have to initialize the random number to a canned value
        random.seed(42)

        # random_number = 49
        self.assertEquals(srv_hostname([
                          {'target': 'avatars4.example.com', 'priority': 10, 'weight': 1, 'port': 83},
                          {'target': 'avatars3.example.com', 'priority': 10, 'weight': 5, 'port': 82},
                          {'target': 'avatars2.example.com', 'priority': 10, 'weight': 10, 'port': 8100},
                          {'target': 'avatars1.example.com', 'priority': 10, 'weight': 50, 'port': 800},
                          {'target': 'avatars.example.com', 'priority': 20, 'weight': 0, 'port': 80},
                          ]),
                          ('avatars1.example.com', 800))

        # random_number = 0
        self.assertEquals(srv_hostname([
                          {'target': 'avatars4.example.com', 'priority': 10, 'weight': 1, 'port': 83},
                          {'target': 'avatars3.example.com', 'priority': 10, 'weight': 0, 'port': 82},
                          {'target': 'avatars2.example.com', 'priority': 20, 'weight': 0, 'port': 81},
                          {'target': 'avatars.example.com', 'priority': 20, 'weight': 0, 'port': 80},
                          ]),
                          ('avatars3.example.com', 82))

        # random_number = 1
        self.assertEquals(srv_hostname([
                          {'target': 'avatars4.example.com', 'priority': 10, 'weight': 0, 'port': 83},
                          {'target': 'avatars3.example.com', 'priority': 10, 'weight': 0, 'port': 82},
                          {'target': 'avatars20.example.com', 'priority': 10, 'weight': 10, 'port': 601},
                          {'target': 'avatars.example.com', 'priority': 20, 'weight': 0, 'port': 80},
                          ]),
                          ('avatars20.example.com', 601))

        # random_number = 40
        self.assertEquals(srv_hostname([
                          {'target': 'avatars4.example.com', 'priority': 10, 'weight': 1, 'port': 83},
                          {'target': 'avatars3.example.com', 'priority': 10, 'weight': 5, 'port': 82},
                          {'target': 'avatars2.example.com', 'priority': 10, 'weight': 10, 'port': 8100},
                          {'target': 'avatars10.example.com', 'priority': 10, 'weight': 30, 'port': 8},
                          {'target': 'avatars1.example.com', 'priority': 10, 'weight': 50, 'port': 800},
                          {'target': 'avatars.example.com', 'priority': 20, 'weight': 0, 'port': 80},
                          ]),
                          ('avatars10.example.com', 8))

    def testHomepage(self):
        c = Client()
        response = c.get('/')
        self.assertEquals(response.status_code, 200)
        self.assertTrue('Federated Open Source Service' in response.content)
