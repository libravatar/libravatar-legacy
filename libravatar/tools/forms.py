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

from django import forms

from libravatar.account.forms import MIN_LENGTH_URL, MAX_LENGTH_URL

class CheckForm(forms.Form):
    email = forms.EmailField(required=False)
    openid = forms.URLField(required=False, verify_exists=False, min_length=MIN_LENGTH_URL, max_length=MAX_LENGTH_URL, label='OpenID')
    size = forms.DecimalField(required=False, min_value=1, max_value=512, decimal_places=0, initial=80)
    not_found = forms.CharField(required=False, label='Default URL')

    def clean(self):
        cleaned_data = self.cleaned_data
        if not cleaned_data.get('email') and not cleaned_data.get('openid'):
            raise forms.ValidationError('You must provide a valid email or OpenID')
        if cleaned_data.get('email') and cleaned_data.get('openid'):
            raise forms.ValidationError('You cannot provide both an email and an OpenID. Choose one!')
        return cleaned_data

class CheckDomainForm(forms.Form):
    domain = forms.CharField()
