# Copyright (C) 2010, 2011, 2013  Francois Marier <francois@libravatar.org>
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

# pylint: disable=W0401,W0614
from django.conf.urls.defaults import patterns, include, handler404, handler500

handler404  # make pyflakes happy, pylint: disable=W0104
handler500  # make pyflakes happy, pylint: disable=W0104

urlpatterns = patterns('',
    (r'^account/', include('libravatar.account.urls')),

    (r'^openid/', include('django_openid_auth.urls')),

    (r'^tools/', include('libravatar.tools.urls')),

    (r'^$', 'libravatar.public.views.home'),
    (r'^resize/', 'libravatar.public.views.resize'),
    (r'^resolve/', 'libravatar.public.views.resolve'),
)
