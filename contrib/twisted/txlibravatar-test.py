#!/usr/bin/python
#
# Test for the txLibravatar module

from twisted.internet import defer, reactor
from twisted.names import client, dns
from twisted.web import server, resource

from txlibravatar import libravatar_url

class TestResource(resource.Resource):
    isLeaf = True
    request = None

    def _print_stuff(self, result):
        (http_avatar, http_missing, https_avatar, https_missing, http_federated_avatar,
         http_federated_missing, https_federated_avatar, https_federated_missing,
         http_openid_avatar, http_openid_missing) = result

        self.request.setHeader("content-type", "text/html")
        self.request.write("<h1>Twisted</h1>")

        self.request.write('Regular HTTP images:<br>')
        self.request.write('<img src="' + http_avatar[1] + '">')
        self.request.write('<img src="' + http_missing[1] + '">')
        self.request.write("<br><br>\n")

        self.request.write('Regular HTTPS images:<br>')
        self.request.write('<img src="' + https_avatar[1] + '">')
        self.request.write('<img src="' + https_missing[1] + '">')
        self.request.write("<br><br>\n")

        self.request.write('Federated HTTP images:<br>')
        self.request.write('<img src="' + http_federated_avatar[1] + '">')
        self.request.write('<img src="' + http_federated_missing[1] + '">')
        self.request.write("<br><br>\n")

        self.request.write('Federated HTTPS images:<br>')
        self.request.write('<img src="' + https_federated_avatar[1] + '">')
        self.request.write('<img src="' + https_federated_missing[1] + '">')
        self.request.write("<br><br>\n")

        self.request.write('Regular HTTP images (OpenID):<br>')
        self.request.write('<img src="' + http_openid_avatar[1] + '">')
        self.request.write('<img src="' + http_openid_missing[1] + '">')
        self.request.write("<br><br>\n")
        self.request.finish()

    def render_GET(self, request):
        self.request = request
        d1 = libravatar_url(email = 'fmarier@gmail.com')
        d2 = libravatar_url(email = 'fmarier+1@gmail.com')
        d3 = libravatar_url(email = 'fmarier@gmail.com', https = True)
        d4 = libravatar_url(email = 'fmarier+1@gmail.com', https = True)
        d5 = libravatar_url(email = 'francois@catalyst.net.nz')
        d6 = libravatar_url(email = 'francois+1@catalyst.net.nz')
        d7 = libravatar_url(email = 'francois@catalyst.net.nz', https = True)
        d8 = libravatar_url(email = 'francois+1@catalyst.net.nz', https = True)
        d9 = libravatar_url(openid = 'https://launchpad.net/~fmarier')
        d10 = libravatar_url(openid = 'https://launchpad.net/~notfmarier')

        dl = defer.DeferredList([d1, d2, d3, d4, d5, d6, d7, d8, d9, d10])
        dl.addCallback(self._print_stuff)
        return server.NOT_DONE_YET

reactor.listenTCP(3000, server.Site(TestResource()))
reactor.run()
