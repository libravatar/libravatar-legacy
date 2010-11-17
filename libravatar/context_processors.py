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

import settings

"""
Default useful variables for the base page template.
"""
def basepage(request):
    context = {}
    context["site_name"] = settings.SITE_NAME
    context["libravatar_version"] = settings.LIBRAVATAR_VERSION
    context["avatar_url"] = settings.AVATAR_URL
    context["secure_avatar_url"] = settings.SECURE_AVATAR_URL
    context["media_url"] = settings.MEDIA_URL
    context["site_url"] = settings.SITE_URL
    context["disable_signup"] = settings.DISABLE_SIGNUP
    return context

