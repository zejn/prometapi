from django.conf.urls import url
from django.views.generic.base import RedirectView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'prometapi.views.home', name='home'),
    # url(r'^prometapi/', include('prometapi.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^promet/$', RedirectView.as_view(url='https://github.com/zejn/prometapi/blob/master/README.rst')),
    url(r'^promet/events/', 'prometapi.views.events'),
    url(r'^promet/burja/', 'prometapi.views.burja'),
    url(r'^promet/burjaznaki/', 'prometapi.views.burjaznaki'),
    url(r'^promet/counters/', 'prometapi.views.counters'),
    url(r'^promet/parkirisca/lpt/', 'prometapi.views.parkirisca_lpt'),
    url(r'^promet/bicikelj/list/', 'prometapi.views.bicikelj'),
    url(r'^promet/gk_to_wgs84/', 'prometapi.views.gk_to_wgs84'),
    url(r'^sos112/spin/', 'prometapi.views.sos112'),
]
