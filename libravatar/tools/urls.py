from django.conf.urls.defaults import *

urlpatterns = patterns('',
    ('check/$', 'libravatar.tools.views.check'),
)
