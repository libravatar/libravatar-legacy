from django.conf.urls.defaults import *

urlpatterns = patterns('',
    ('login/$', 'django.contrib.auth.views.login', {'template_name': 'account/login.html'}),
    ('logout/$', 'django.contrib.auth.views.logout_then_login'),
    ('password_change/$', 'django.contrib.auth.views.password_change', {'template_name': 'account/password_change.html'}),
    ('password_change_done/$', 'django.contrib.auth.views.password_change_done', {'template_name': 'account/password_change_done.html'}),

    ('add_email/$', 'libravatar.account.views.add_email'),
    ('confirm_email/$', 'libravatar.account.views.confirm_email'),
    (r'^(?P<email_id>\d+)/remove_confirmed_email/$', 'libravatar.account.views.remove_confirmed_email'),
    (r'^(?P<email_id>\d+)/remove_unconfirmed_email/$', 'libravatar.account.views.remove_unconfirmed_email'),

    ('new/$', 'libravatar.account.views.new'),
    ('profile/$', 'libravatar.account.views.profile'),

    ('upload_photo/$', 'libravatar.account.views.upload_photo'),
    (r'^(?P<photo_id>\d+)/delete_photo/$', 'libravatar.account.views.delete_photo'),
)
