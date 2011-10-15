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

from libravatar.account.models import ConfirmedEmail, UnconfirmedEmail
from django.contrib import admin


class ConfirmedEmailAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'add_date')


class UnconfirmedEmailAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'verification_key', 'add_date']

admin.site.register(ConfirmedEmail, ConfirmedEmailAdmin)
admin.site.register(UnconfirmedEmail, UnconfirmedEmailAdmin)
