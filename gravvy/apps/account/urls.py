from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from gravvy.apps.account import views

# URL structure inspired by github API: https://developer.github.com/v3/users/

urlpatterns = [
                       
    # ------------------------------------------------------
    # User List and Details, and Sub-Lists
    # ------------------------------------------------------
    # user list
    url(r'^users/$', views.UserList.as_view(), name='user-list'),
    
    # user details and associated lists
    url(r'^users/(?P<phone_number>\+\d{1,15})/$',
        views.UserDetail.as_view(), 
        name='user-detail'),
    
    url(r'^users/(?P<phone_number>\+\d{1,15})/videos/$',
        views.UserVideoList.as_view(), 
        name='user-video-list'),
    
    # ------------------------------------------------------
    # Authenticated User's Details and Associated Sub-Lists
    # ------------------------------------------------------
    url(r'^user/$', 
        views.AuthenticatedUserDetail.as_view(), 
        name='user-auth-detail'),
    
    url(r'^user/videos/$',
        views.AuthenticatedUserVideoList.as_view(), 
        name='user-auth-video-list'),
    
    url(r'^user/activities/$',
        views.AuthenticatedUserActivityList.as_view(), 
        name='user-auth-activity-list'),
    
    url(r'^user/recentcontacts/$',
        views.AuthenticatedUserRecentContactList.as_view(), 
        name='user-auth-recentcontacts-list'),
    
    # ------------------------------------------------------
    # Account and Credentials Manangement endpoints
    # ------------------------------------------------------
    # collection of account management endpoints
    url(r'^account/$', views.account_root, name='account_root'),
    
    # obtain auth token given a username and password
    url(r'^account/auth/$', 
        views.ObtainExpiringAuthToken.as_view(),
        name='obtain_auth_token'),
    
    # activate a user given a verification_code
    url(r'^account/activate/$', 
        views.ActivateAccount.as_view(),
        name='activate_user'),
    ]

urlpatterns = format_suffix_patterns(urlpatterns)
