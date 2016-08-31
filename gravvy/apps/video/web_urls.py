"""
URL patterns that aren't included in the REST API
"""

from django.conf.urls import url
from gravvy.apps.video import views

urlpatterns = [
    # video details
    url(r'^v/(?P<hash_key>[\w.+-]+)/$', 
        views.videodetail, name='web-video-detail'),
    
    # video clip web upload
    url(r'^v/(?P<hash_key>[\w.+-]+)/upload/$', 
        views.videoclipupload, name='web-video-clip-upload'),
]
