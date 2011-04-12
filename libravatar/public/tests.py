import unittest

from views import lookup_avatar_server, mimetype_format # pylint: disable=W0403

class PublicTestCase(unittest.TestCase):
    def setUp(self):
        pass # Nothing to do

    def testMimetypes(self):
        self.assertEquals(mimetype_format('JPEG'), 'image/jpeg')
        self.assertEquals(mimetype_format('PNG'), 'image/png')
        self.assertEquals(mimetype_format('GIF'), 'image/jpeg')

    def testDnsLookup(self):
        self.assertEquals(lookup_avatar_server('', False), None)
        self.assertEquals(lookup_avatar_server(None, False), None)
        self.assertEquals(lookup_avatar_server('invalid', True), None)
        self.assertEquals(lookup_avatar_server('example.com', False), None)
        self.assertEquals(lookup_avatar_server('example.com', True), None)
        self.assertEquals(lookup_avatar_server('catalyst.net.nz', False), 'static.avatars.catalyst.net.nz')
        self.assertEquals(lookup_avatar_server('catalyst.net.nz', True), None)
