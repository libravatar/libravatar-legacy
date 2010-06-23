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

urlpatterns = patterns('',
    ('login/$', 'django.contrib.auth.views.login', {'template_name': 'account/login.html'}),
    ('logout/$', 'django.contrib.auth.views.logout', {'next_page' : '/'}),
    ('password_change/$', 'django.contrib.auth.views.password_change', {'template_name': 'account/password_change.html'}),
    ('password_change_done/$', 'django.contrib.auth.views.password_change_done', {'template_name': 'account/password_change_done.html'}),

    ('add_email/$', 'libravatar.account.views.add_email'),
    ('confirm_email/$', 'libravatar.account.views.confirm_email'),
    (r'^(?P<email_id>\d+)/remove_confirmed_email/$', 'libravatar.account.views.remove_confirmed_email'),
    (r'^(?P<email_id>\d+)/remove_unconfirmed_email/$', 'libravatar.account.views.remove_unconfirmed_email'),

    ('new/$', 'libravatar.account.views.new'),
    ('profile/$', 'libravatar.account.views.profile'),
    ('profile_success/$', 'libravatar.account.views.successfully_authenticated'),

    (r'^(?P<email_id>\d+)/assign_photo/$', 'libravatar.account.views.assign_photo'),
    (r'^(?P<user_id>\d+)/import_photo/$', 'libravatar.account.views.import_photo'),
    ('upload_photo/$', 'libravatar.account.views.upload_photo'),
    ('crop_photo/$', 'libravatar.account.views.crop_photo'),
    (r'^(?P<photo_id>\d+)/crop_photo/?$', 'libravatar.account.views.crop_photo'),
    (r'^(?P<photo_id>\d+)/delete_photo/$', 'libravatar.account.views.delete_photo'),

    # Default page
    (r'^$', 'libravatar.account.views.profile'),
)
