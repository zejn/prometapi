from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'prometapi.views.home', name='home'),
    # url(r'^prometapi/', include('prometapi.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^promet/$', 'django.views.generic.simple.redirect_to', {'url': 'https://github.com/zejn/prometapi/blob/master/README.rst'}),
    url(r'^promet/events/', 'prometapi.views.events'),
    url(r'^promet/burja/', 'prometapi.views.burja'),
    url(r'^promet/burjaznaki/', 'prometapi.views.burjaznaki'),
    url(r'^promet/counters/', 'prometapi.views.counters'),
    url(r'^promet/parkirisca/lpt/', 'prometapi.views.parkirisca_lpt'),
)
