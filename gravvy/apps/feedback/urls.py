from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns
from gravvy.apps.feedback import views

urlpatterns = patterns('',
                       # submit feedback
                       url(r'^feedbacks/$', views.FeedbackList.as_view(), 
                           name='feedback-list'),
                       )

urlpatterns = format_suffix_patterns(urlpatterns)
