// Test for the Libravatar node.js module

var http = require('http');
var libravatar = require('libravatar');

var data = [
    {name: 'http_avatar', email: 'fmarier@gmail.com', openid: null, https: false},
    {name: 'http_missing', email: 'fmarier+1@gmail.com', openid: null, https: false},
    {name: 'https_avatar', email: 'fmarier@gmail.com', openid: null, https: true},
    {name: 'https_missing', email: 'fmarier+1@gmail.com', openid: null, https: true},
    {name: 'http_federated_avatar', email: 'francois@catalyst.net.nz', openid: null, https: false},
    {name: 'http_federated_missing', email: 'francois+1@catalyst.net.nz', openid: null, https: false},
    {name: 'https_federated_avatar', email: 'francois@catalyst.net.nz', openid: null, https: true},
    {name: 'https_federated_missing', email: 'francois+1@catalyst.net.nz', openid: null, https: true},
    {name: 'http_openid_avatar', email: null, openid : 'https://launchpad.net/~fmarier', https: false},
    {name: 'http_openid_missing', email: null, openid : 'https://launchpad.net/~notfmarier', https: false},
];

var urls = {};

var server = http.createServer(function (req, res) {
    var count = 0;
    data.forEach(function(v) {
        libravatar.url(v.email, v.openid, {}, v.https, function(error, url) {
            count++;

            urls[v.name] = url;

            if (count === data.length) {
                res.writeHead(200, {'Content-Type': 'text/html'});
                res.write('<h1>node-libravatar</h1>');

                res.write('Regular HTTP images:<br>');
                res.write('<img src="' + urls['http_avatar'] + '">');
                res.write('<img src="' + urls['http_missing'] + '">');
                res.write("<br><br>\n");

                res.write('Regular HTTPS images:<br>');
                res.write('<img src="' + urls['https_avatar'] + '">');
                res.write('<img src="' + urls['https_missing'] + '">');
                res.write("<br><br>\n");

                res.write('Federated HTTP images:<br>');
                res.write('<img src="' + urls['http_federated_avatar'] + '">');
                res.write('<img src="' + urls['http_federated_missing'] + '">');
                res.write("<br><br>\n");

                res.write('Federated HTTPS images:<br>');
                res.write('<img src="' + urls['https_federated_avatar'] + '">');
                res.write('<img src="' + urls['https_federated_missing'] + '">');
                res.write("<br><br>\n");

                res.write('Regular HTTP images (OpenID):<br>');
                res.write('<img src="' + urls['http_openid_avatar'] + '">');
                res.write('<img src="' + urls['http_openid_missing'] + '">');
                res.write("<br><br>\n");

                res.end();
            }
        });
    });
});

server.listen(3000, "127.0.0.1");
console.log('Server running at http://127.0.0.1:3000/');
