from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from gravvy.apps.video import views

urlpatterns = [
                       
    # ------------------------------------------------------
    # Video List and Details
    # ------------------------------------------------------
    # video list
    url(r'^videos/$', views.VideoList.as_view(), name='video-list'),
    
    # video details
    url(r'^videos/(?P<hash_key>[\w.+-]+)/$', 
        views.VideoDetail.as_view(), 
        name='video-detail'),
    
    # record a video like
     url(r'^videos/(?P<hash_key>[\w.+-]+)/like/$', 
        views.VideoDetailLike.as_view(), 
        name='video-detail-like'),
    
    # record a video play
    url(r'^videos/(?P<hash_key>[\w.+-]+)/play/$', 
        views.VideoDetailPlay.as_view(), 
        name='video-detail-play'),
    
    # acknowledge viewing of video notifications
    url(r'^videos/(?P<hash_key>[\w.+-]+)/clearnotifications/$', 
        views.VideoDetailClearNotifications.as_view(), 
        name='video-detail-clearnotifications'),
    
    # ------------------------------------------------------
    # Video Clip Management
    # ------------------------------------------------------
    # all clips of a video
    url(r'^videos/(?P<hash_key>[\w.+-]+)/clips/$', 
        views.VideoClipList.as_view(), 
        name='video-clip-list'),
    
    # clip details
    url(r'^videos/(?P<hash_key>[\w.+-]+)/clips/(?P<pk>\d+)/$', 
        views.VideoClipDetail.as_view(), 
        name='video-clip-detail'),
    
    # ------------------------------------------------------
    # Video User Management
    # ------------------------------------------------------
    # all users of a video
    url(r'^videos/(?P<hash_key>[\w.+-]+)/users/$', 
        views.VideoUserList.as_view(), 
        name='video-user-list'),
    
    # video user detail
    url(r'^videos/(?P<hash_key>[\w.+-]+)/users/(?P<phone_number>\+\d{1,15})/$', 
        views.VideoUserDetail.as_view(), 
        name='video-user-detail'),
    
    # ------------------------------------------------------
    # Video Like Management
    # ------------------------------------------------------
    # all likes of a video
    url(r'^videos/(?P<hash_key>[\w.+-]+)/likes/$', 
        views.VideoLikeList.as_view(), 
        name='video-like-list'),
    ]

urlpatterns = format_suffix_patterns(urlpatterns)
