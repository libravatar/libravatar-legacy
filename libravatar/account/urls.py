# Copyright (C) 2011, 2013, 2015, 2016  Francois Marier <francois@libravatar.org>
# Copyright (C) 2010  Francois Marier <francois@libravatar.org>
#                     Jonathan Harker <jon@jon.geek.nz>
#                     Brett Wilkins <bushido.katana@gmail.com>
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

from django.conf.urls import url, patterns

# pylint: disable=invalid-name
urlpatterns = patterns('',
                       url('login/$', 'django.contrib.auth.views.login',
                           {'template_name': 'account/login.html'},
                           name='login'),
                       url('logout/$', 'django.contrib.auth.views.logout',
                           {'next_page': '/'},
                           name='logout'),  # must be the last pattern using this view!
                       url('password_change/$',
                           'django.contrib.auth.views.password_change',
                           {'template_name': 'account/password_change.html'},
                           name='password_change'),
                       url('password_change_done/$',
                           'django.contrib.auth.views.password_change_done',
                           {'template_name': 'account/password_change_done.html'},
                           name='password_change_done'),
                       url('password_set/$',
                           'libravatar.account.views.password_set'),

                       url('add_email/$',
                           'libravatar.account.views.add_email'),
                       url('add_openid/$',
                           'libravatar.account.views.add_openid'),
                       url('confirm_email/$',
                           'libravatar.account.views.confirm_email'),
                       url(r'^(?P<openid_id>\d+)/confirm_openid/$',
                           'libravatar.account.views.confirm_openid'),
                       url(r'^(?P<openid_id>\d+)/redirect_openid/$',
                           'libravatar.account.views.redirect_openid'),
                       url(r'^(?P<email_id>\d+)/remove_confirmed_email/$',
                           'libravatar.account.views.remove_confirmed_email'),
                       url(r'^(?P<email_id>\d+)/remove_unconfirmed_email/$',
                           'libravatar.account.views.remove_unconfirmed_email'),
                       url(r'^(?P<openid_id>\d+)/remove_confirmed_openid/$',
                           'libravatar.account.views.remove_confirmed_openid'),
                       url(r'^(?P<openid_id>\d+)/remove_unconfirmed_openid/$',
                           'libravatar.account.views.remove_unconfirmed_openid'),

                       url('delete/$', 'libravatar.account.views.delete'),
                       url('export/$', 'libravatar.account.views.export'),
                       url('new/$', 'libravatar.account.views.new'),
                       url('password_reset/$',
                           'libravatar.account.views.password_reset',
                           name='password_reset'),
                       url('password_reset_confirm/$',
                           'libravatar.account.views.password_reset_confirm',
                           name='password_reset_confirm'),
                       url('profile/$', 'libravatar.account.views.profile'),
                       url('profile_success/$',
                           'libravatar.account.views.successfully_authenticated'),

                       url(r'^(?P<email_id>\d+)/assign_photo_email/$',
                           'libravatar.account.views.assign_photo_email'),
                       url(r'^(?P<openid_id>\d+)/assign_photo_openid/$',
                           'libravatar.account.views.assign_photo_openid'),
                       url(r'^(?P<user_id>\d+)/import_photo/$',
                           'libravatar.account.views.import_photo'),
                       url('upload_photo/$',
                           'libravatar.account.views.upload_photo'),
                       url('crop_photo/$',
                           'libravatar.account.views.crop_photo'),
                       url(r'^(?P<photo_id>\d+)/crop_photo/?$',
                           'libravatar.account.views.crop_photo'),
                       url(r'^(?P<photo_id>\d+)/auto_crop/?$',
                           'libravatar.account.views.auto_crop'),
                       url(r'^(?P<photo_id>\d+)/delete_photo/$',
                           'libravatar.account.views.delete_photo'),

                       # Default page
                       url(r'^$', 'libravatar.account.views.profile'),
                      )
