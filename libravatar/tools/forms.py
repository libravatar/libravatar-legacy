# Copyright (C) 2010, 2011  Francois Marier <francois@libravatar.org>
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

from django import forms
from django.utils.translation import ugettext_lazy as _

from libravatar.account.forms import MIN_LENGTH_URL, MAX_LENGTH_URL

class CheckForm(forms.Form):
    email = forms.EmailField(label=_('Email'), required=False)
    openid = forms.URLField(label=_('OpenID'), required=False, verify_exists=False, min_length=MIN_LENGTH_URL, max_length=MAX_LENGTH_URL)
    size = forms.DecimalField(label=_('Size'), required=False, min_value=1, max_value=512, decimal_places=0, initial=80)
    not_found = forms.CharField(label=_('Default URL'), required=False)

    def clean(self):
        cleaned_data = self.cleaned_data
        if not cleaned_data.get('email') and not cleaned_data.get('openid'):
            raise forms.ValidationError(_('You must provide a valid email or OpenID'))
        if cleaned_data.get('email') and cleaned_data.get('openid'):
            raise forms.ValidationError(_('You cannot provide both an email and an OpenID. Choose one!'))
        return cleaned_data

class CheckDomainForm(forms.Form):
    domain = forms.CharField(label=_('Domain'))
