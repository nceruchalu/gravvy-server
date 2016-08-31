from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView

# REST API URLS
api_urlpatterns = [
    url(r'^$', 'gravvy.views.api_root', name='api_root'),
    url(r'', include('gravvy.apps.account.urls')),
    url(r'', include('gravvy.apps.video.urls')),
    url(r'', include('gravvy.apps.feedback.urls')),
    url(r'', include('gravvy.apps.push.urls')),
    # login and logout views for the browsable API
    url(r'^browse/',include('rest_framework.urls', namespace='rest_framework')),
    ]


urlpatterns = [
    
    # REST API URLS with version number
    url(r'^api/v1/', include(api_urlpatterns)),
    
    # Regular web URLs
    url(r'', include('gravvy.apps.video.web_urls')),
    
    url(r'^$', TemplateView.as_view(template_name="home.html"), name='home'),
    url(r'^terms/$', TemplateView.as_view(template_name="terms.html"), 
        name='terms'),
    url(r'^privacy/$', TemplateView.as_view(template_name="privacy.html"),
        name='privacy'),
    
    url(r'^admin/', include(admin.site.urls)),
]
