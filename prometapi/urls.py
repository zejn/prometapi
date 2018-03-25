from django.conf import settings
from django.conf.urls import url
from django.views.generic.base import RedirectView
from prometapi import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', views.home, name='home'),
    # url(r'^prometapi/', include('prometapi.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^promet/$', RedirectView.as_view(url='https://github.com/zejn/prometapi/blob/master/README.rst')),
    url(r'^promet/events/$', views.events),
    url(r'^promet/cameras/', views.cameras),
    url(r'^promet/burja/', views.burja),
    url(r'^promet/burjaznaki/', views.burjaznaki),
    url(r'^promet/counters/', views.counters),
    url(r'^promet/parkirisca/lpt/', views.parkirisca_lpt),
    url(r'^promet/bicikelj/list/', views.bicikelj),
    url(r'^promet/gk_to_wgs84/', views.gk_to_wgs84),
    url(r'^sos112/spin/', views.sos112),
]

if settings.DEBUG:
    urlpatterns += [
        url(r'^debug/promet/', views.debug_promet),
        url(r'^debug/compat/', views.debug_compat)
    ]
