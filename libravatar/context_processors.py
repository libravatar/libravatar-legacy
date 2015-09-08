# Copyright (C) 2011, 2012, 2013  Francois Marier <francois@libravatar.org>
# Copyright (C) 2010  Jonathan Harker <jon@jon.geek.nz>
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

from libravatar import settings


# Default useful variables for the base page template.
def basepage(request):
    context = {}
    context['avatar_url'] = settings.AVATAR_URL
    if '1' == request.GET.get('embedded'):
        context['base_template'] = 'base_embedded.html'
    else:
        context['base_template'] = 'base.html'
    context['contact_us'] = settings.CONTACT_US
    context['dev_email'] = settings.DEV_EMAIL
    context['disable_signup'] = settings.DISABLE_SIGNUP
    context['embedded'] = request.GET.get('embedded')
    context['libravatar_version'] = settings.LIBRAVATAR_VERSION
    context['secure_avatar_url'] = settings.SECURE_AVATAR_URL
    context['security_url'] = settings.SECURITY_URL
    context['site_name'] = settings.SITE_NAME
    context['site_url'] = settings.SITE_URL
    context['support_email'] = settings.SUPPORT_EMAIL
    if 'browserid_user' in request.session:
        context['browserid_user'] = request.session['browserid_user']
    else:
        context['browserid_user'] = ''
    return context
