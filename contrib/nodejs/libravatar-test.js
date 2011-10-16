// Test for the Libravatar node.js module

var http = require('http');
var libravatar = require('libravatar');

var server = http.createServer(function (req, res) {
  libravatar.url('fmarier@gmail.com', openid=null, {}, https=false,
    function (http_avatar) {
      libravatar.url('fmarier+1@gmail.com', openid=null, {}, https=false,
        function (http_missing) {
          libravatar.url('fmarier@gmail.com', openid=null, {}, https=true,
            function (https_avatar) {
              libravatar.url('fmarier+1@gmail.com', openid=null, {}, https=true,
                function (https_missing) {
                  libravatar.url('francois@catalyst.net.nz', openid=null, {}, https=false,
                    function (http_federated_avatar) {
                      libravatar.url('francois+1@catalyst.net.nz', openid=null, {}, https=false,
                        function (http_federated_missing) {
                          libravatar.url('francois@catalyst.net.nz', openid=null, {}, https=true,
                            function (https_federated_avatar) {
                              libravatar.url('francois+1@catalyst.net.nz', openid=null, {}, https=true,
                                function (https_federated_missing) {
                                  libravatar.url(email=null, 'https://launchpad.net/~fmarier', {}, https=false,
                                    function (http_openid_avatar) {
                                      libravatar.url(email=null, 'https://launchpad.net/~notfmarier', {}, https=false,
                                        function (http_openid_missing) {
                                            res.writeHead(200, {'Content-Type': 'text/html'});
                                            res.write('<h1>node-libravatar</h1>');

                                            res.write('Regular HTTP images:<br>');
                                            res.write('<img src="' + http_avatar + '">');
                                            res.write('<img src="' + http_missing + '">');
                                            res.write("<br><br>\n");

                                            res.write('Regular HTTPS images:<br>');
                                            res.write('<img src="' + https_avatar + '">');
                                            res.write('<img src="' + https_missing + '">');
                                            res.write("<br><br>\n");

                                            res.write('Federated HTTP images:<br>');
                                            res.write('<img src="' + http_federated_avatar + '">');
                                            res.write('<img src="' + http_federated_missing + '">');
                                            res.write("<br><br>\n");

                                            res.write('Federated HTTPS images:<br>');
                                            res.write('<img src="' + https_federated_avatar + '">');
                                            res.write('<img src="' + https_federated_missing + '">');
                                            res.write("<br><br>\n");

                                            res.write('Regular HTTP images (OpenID):<br>');
                                            res.write('<img src="' + http_openid_avatar + '">');
                                            res.write('<img src="' + http_openid_missing + '">');
                                            res.write("<br><br>\n");

                                            res.end();
                                        });
                                    });
                                });
                            });
                        });
                    });
                });
            });
        });
    });
});

server.listen(3000, "127.0.0.1");
console.log('Server running at http://127.0.0.1:3000/');
