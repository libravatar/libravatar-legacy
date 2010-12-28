# Copyright (C) 2010  Francois Marier <francois@libravatar.org>
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

from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^account/', include('libravatar.account.urls')),
    (r'^tools/', include('libravatar.tools.urls')),

    (r'^$', 'libravatar.public.views.home'),
    (r'^resize/', 'libravatar.public.views.resize'),
    (r'^resolve/', 'libravatar.public.views.resolve'),
)
