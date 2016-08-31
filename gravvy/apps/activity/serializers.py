
from rest_framework import serializers

from gravvy.apps.activity.models import Activity

from gravvy.apps.account.models import User
from gravvy.apps.account.serializers import UserMinimalSerializer

from gravvy.apps.video.models import Clip, Video
from gravvy.apps.video.serializers import (
    ClipMinimalSerializer, VideoMinimalSerializer)

class ActivityRelatedField(serializers.RelatedField):
    """
    A custom field to use for the `target` and `object` generic relationships
    """
    
    def to_representation(self, value):
        """
        Serialize user instances using a user serializer, clip instances using a
        clip serializer, and video Instances using a video serializer.
        """
        if isinstance(value, User):
            serializer = UserMinimalSerializer(value)
        elif isinstance(value, Clip):
            serializer = ClipMinimalSerializer(value)
        elif isinstance(value, Video):
            serializer = VideoMinimalSerializer(value)
        else:
            raise Exception('Unexpected type of target or object')
        
        return serializer.data
            

class ActivitySerializer(serializers.ModelSerializer):
    """
    Serializer to be used for getting Activities
    """
    actor = UserMinimalSerializer(read_only=True)
    object = ActivityRelatedField(read_only=True)
    target = ActivityRelatedField(read_only=True)
    
    class Meta:
        model = Activity
        fields = ('id', 'actor', 'verb', 'object', 'target', 'created_at',)
        read_only_fields = ('verb', 'created_at',)

