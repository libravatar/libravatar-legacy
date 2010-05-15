from django.conf.urls.defaults import *

urlpatterns = patterns('',
    ('login/$', 'django.contrib.auth.views.login', {'template_name': 'account/login.html'}),
    ('logout/$', 'django.contrib.auth.views.logout_then_login'),

    ('password_change/$', 'django.contrib.auth.views.password_change', {'template_name': 'account/password_change.html'}),
    ('password_change_done/$', 'django.contrib.auth.views.password_change_done', {'template_name': 'account/password_change_done.html'}),

    ('profile/$', 'libravatar.account.views.profile'),
)
