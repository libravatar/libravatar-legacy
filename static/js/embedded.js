/**
 * Support file for Libravatar
 * @source: https://code.launchpad.net/libravatar
 *
 * @licstart
 * Copyright (C) 2013 Francois Marier <francois@libravatar.org>
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

var LOGGED_IN_PAGE = '/account/profile_embedded';
var LOGGED_OUT_PAGE = '/account/logout_embedded';

$('#close-button').bind('click', function () {window.close();});
$('#cancel-link').bind('click', function () {window.close();});
