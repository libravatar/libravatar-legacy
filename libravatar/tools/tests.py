import re
import unittest

from views import lookup_ip_address # pylint: disable=W0403

def match_regexp(result, regexp):
    return re.match(regexp, result)

class ToolsTestCase(unittest.TestCase):
    def setUp(self):
        pass # Nothing to do

    def testIpLookup(self):
        self.assertTrue(match_regexp(lookup_ip_address('www.google.com', False), r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'))
        self.assertTrue(match_regexp(lookup_ip_address('ipv6.google.com', True), r'^[0-9a-f:]+$'))
