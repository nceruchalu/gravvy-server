from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from gravvy.apps.push import views

urlpatterns = [
    url(r'^push/$', views.push_root, 
        name='push_root'),
                       
    # register an iOS device's APNS device token
    url(r'^push/apns/$', 
        views.RegisterAPNSDevice.as_view(),
        name='push_register_apns'),
    ]

urlpatterns = format_suffix_patterns(urlpatterns)
