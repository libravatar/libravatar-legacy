from libravatar.account.models import ConfirmedEmail, UnconfirmedEmail
from django.contrib import admin

class ConfirmedEmailAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'add_date')

class UnconfirmedEmailAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'verification_key', 'add_date']

admin.site.register(ConfirmedEmail, ConfirmedEmailAdmin)
admin.site.register(UnconfirmedEmail, UnconfirmedEmailAdmin)
