from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^account/', include('libravatar.account.urls')),
    (r'^tools/', include('libravatar.tools.urls')),
    (r'^$', 'libravatar.public.views.home'),

    (r'^admin/', include(admin.site.urls)),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
)
