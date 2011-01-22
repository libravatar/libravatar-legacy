// Libravatar Images
// version 0.1
// 2011-01-22
// Copyright (c) 2011, Francois Marier <fmarier@gmail.com>
// Released under the GNU GPL version 3 or later
// http://www.gnu.org/copyleft/gpl.html
//
// --------------------------------------------------------------------
// This is a Greasemonkey user script.  To install it, you need
// Greasemonkey 0.8 or later: http://greasemonkey.mozdev.org/
// Then restart Firefox and revisit this script.
// Under Tools, there will be a new menu item to "Install User Script".
// Accept the default configuration and install.
//
// To uninstall, go to Tools/Manage User Scripts,
// select "Libravatar Images", and click Uninstall.
// --------------------------------------------------------------------
//
// ==UserScript==
// @name          Libravatar Images
// @namespace     http://www.libravatar.org
// @description   Replace gravatar.com images with libravatar.org ones
// @include       *
// ==/UserScript==

(function() {
     images = document.evaluate('//img[contains(@src, "")]', document, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null);

     for (var i=0; i < images.snapshotLength; i++) {
	 var image = images.snapshotItem(i);
	 var src = image.src;

	 if (!src) {
             continue;
         }

	 if (src.indexOf("http://www.gravatar.com/avatar/") != -1) {
             image.src = src.replace("http://www.gravatar.com/avatar/", "http://cdn.libravatar.org/avatar/");
         }
	 else if (src.indexOf("https://secure.gravatar.com/avatar/") != -1) {
             image.src = src.replace("https://secure.gravatar.com/avatar/", "https://seccdn.libravatar.org/avatar/");
         }
	 else if (src.indexOf("http://www.gravatar.com/avatar.php?gravatar_id=") != -1) {
             image.src = src.replace(new RegExp("^http://www\\.gravatar\\.com/avatar\\.php\\?gravatar_id=([a-f0-9A-F]+)&?"), "http://cdn.libravatar.org/avatar/$1?");
         }
     }

})();

// DEBUG: make sure the page has no errors
//alert('done');
