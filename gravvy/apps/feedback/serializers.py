"""
Provides a way of serializing and deserializing the feedback app model
instances into representations such as json.
"""

from rest_framework import serializers
from gravvy.apps.feedback.models import Feedback

class FeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer to be used for submitting Feedback
    """
    
    class Meta:
        model = Feedback
        fields = ('body',)
    
