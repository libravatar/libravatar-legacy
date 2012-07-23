/**
 * Support file for Libravatar
 * @source: https://code.launchpad.net/libravatar
 *
 * @licstart
 * Copyright (C) 2011, 2012 Francois Marier <francois@libravatar.org>
 *
 * The JavaScript code in this page is free software: you can
 * redistribute it and/or modify it under the terms of the GNU Affero
 * General Public License as published by the Free Software
 * Foundation, either version 3 of the License, or (at your option)
 * any later version. The code is distributed WITHOUT ANY WARRANTY;
 * without even the implied warranty of MERCHANTABILITY or FITNESS FOR
 * A PARTICULAR PURPOSE.  See the GNU Affero General Public License
 * for more details.
 *
 * As an additional permission under GNU AGPL version 3 section 7, you
 * may distribute non-source (e.g., minimized or compacted) forms of
 * that code without the copy of the GNU AGPL normally required by
 * section 4, provided you include this license notice and a URL
 * through which recipients can access the Corresponding Source.
 * @licend
 */

"use strict";

// Autofocus the right field on forms
if (document.forms.login) {
    if (document.forms.login.username) {
        document.forms.login.username.focus();
    } else if (document.forms.login.openid_identifier) {
        document.forms.login.openid_identifier.focus();
    }
} else if (document.forms.addemail) {
    document.forms.addemail.email.focus();
} else if (document.forms.addopenid) {
    document.forms.addopenid.openid.focus();
} else if (document.forms.changepassword) {
    document.forms.changepassword.old_password.focus();
} else if (document.forms.deleteaccount) {
    if (document.forms.deleteaccount.password) {
        document.forms.deleteaccount.password.focus();
    }
} else if (document.forms.lookup) {
    if (document.forms.lookup.email) {
        document.forms.lookup.email.focus();
    } else if (document.forms.lookup.domain) {
        document.forms.lookup.domain.focus();
    }
} else if (document.forms.newaccount) {
    document.forms.newaccount.username.focus();
} else if (document.forms.reset) {
    document.forms.reset.email.focus();
}

var deleteaccount_button = $('#deleteaccount-button');
var is_deleteaccount = false;
if (deleteaccount_button.length > 0) {
    is_deleteaccount = true;
}

var is_addemail = false;
if ($('#form-addemail').length > 0) {
    is_addemail = true;
}
var email_requested = false;

if (navigator.id) {
    var browserid_user = $('#browserid-user').text();
    if (browserid_user === '') {
        browserid_user = null;
    }

    // Show BrowserID option and make links clickable
    $('#browserid-option').show();
    var browserid_link = $('#browserid-link');
    browserid_link.attr('href', '#');
    browserid_link.bind('click', browserid_login);
    var logout_link = $('#logout-link');
    if (browserid_user && !is_addemail) {
        logout_link.attr('href', '#');
        logout_link.bind('click', browserid_logout);
    }
    deleteaccount_button.bind('click', browserid_logout);

    var post_url = '/account/login_browserid/';
    if (is_addemail) {
        post_url = '/account/add_browserid/';
    }

    navigator.id.watch({
        loggedInUser: browserid_user,
        onlogin: function (assertion) {
            if (assertion && (!is_addemail || email_requested)) {
                $.post(post_url, {assertion: assertion}, function (data) {
                    if (data.success === true) {
                        if (data.user !== browserid_user) {
                            window.location = '/account/profile/';
                        }
                    } else {
                        alert(data.error);
                        browserid_user = null; // make sure onlogout doesn't redirect
                        browserid_logout();
                    }
                });
            }
        },
        onlogout: function () {
            if (browserid_user && !is_deleteaccount) {
                window.location = '/account/logout/';
            }
        }
    });
}

// For main BrowserID functionality
function browserid_login() {
    email_requested = true;
    navigator.id.request();
}
function browserid_logout() {
    navigator.id.logout();
}
