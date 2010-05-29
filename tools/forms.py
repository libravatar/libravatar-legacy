from django import forms

class CheckForm(forms.Form):
    email = forms.EmailField()
