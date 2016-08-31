"""
Provides a way of serializing and deserializing the video app model 
instances into representations such as json.
"""

from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from rest_framework import serializers

from gravvy.utils import human_readable_size
from gravvy.apps.video.models import Video, Clip, VideoUsers
from gravvy.apps.account.serializers import (
    UserPublicSerializer, UserNumberSerializer, UserMinimalSerializer)
from gravvy.apps.activity import activity
from gravvy.apps.activity.models import Activity

class ClipSerializer(serializers.ModelSerializer):
    """
    Serializer to be used for getting and updating Clips.
    """
    # cannot use HyperlinkedIdentityField for the url field because it doesn't
    # work with multi-parameter URLs
    url =  serializers.SerializerMethodField()
    
    owner = UserPublicSerializer(read_only=True)
    photo_thumbnail = serializers.SerializerMethodField()
        
    class Meta:
        model = Clip
        fields = ('url', 'id', 'owner', 'order', 'mp4', 'photo', 
                  'photo_thumbnail', 'duration', 'updated_at')
        read_only_fields = ('id', 'order', 'updated_at')
        extra_kwargs = {'photo': {'write_only': True}}
                
    def get_url(self, obj):
        """
        Build out the absolute URI of the clip object including the host and
        protocol.
        """
        request = self.context['request']
        return request.build_absolute_uri(obj.get_absolute_url())
        
    def validate_mp4(self, value):
        """
        Ensure mp4 is within specified size and is a valid file type
        """
        vidfile = value
        if vidfile.size > settings.MAX_VIDEO_CLIP_SIZE:
            raise serializers.ValidationError(
                "Ensure this file's size is at most %s (it is %s)."
                % (human_readable_size(settings.MAX_VIDEO_CLIP_SIZE), 
                   human_readable_size(vidfile.size)))
        
        if hasattr(vidfile, 'content_type') and \
                    (vidfile.content_type not in settings.VIDEO_CLIP_FORMATS):
                raise serializers.ValidationError(
                    "Upload a valid mp4 file. Detected file type: %s" 
                    % vidfile.content_type)
        return value
        
    def validate_photo(self, value):
        """
        Check that the uploaded file size is within allowed limits
        """
        imgfile = value
        if imgfile and imgfile.size > settings.MAX_IMAGE_SIZE:
            raise serializers.ValidationError(
                "Ensure this file's size is at most %s (it is %s)."
                % (human_readable_size(settings.MAX_IMAGE_SIZE), 
                   human_readable_size(imgfile.size)))
        return value
    
    def get_photo_thumbnail(self, obj):
        """
        Get the absolute URI of the clips's photo thumbnail
        """
        return obj.get_photo_thumbnail_url()
     

class VideoSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer to be used for getting and updating Videos.
    """
    # url field should lookup by 'hash key' not the 'pk'
    url = serializers.HyperlinkedIdentityField(
        view_name='video-detail', lookup_field='hash_key')
    
    owner = UserPublicSerializer(read_only=True)
    photo_thumbnail = serializers.SerializerMethodField()
    photo_small_thumbnail = serializers.SerializerMethodField()
    
    liked = serializers.SerializerMethodField()
    new_likes_count = serializers.SerializerMethodField()
    new_clips_count = serializers.SerializerMethodField()
    membership_status = serializers.SerializerMethodField()
        
    clips = ClipSerializer(many=True, source='get_clips')
    
    # Show links to the video's sub-collections that can't be fully embedded
    users_url = serializers.HyperlinkedIdentityField(
        view_name='video-user-list', lookup_field='hash_key')
    
    class Meta:
        model = Video
        fields = ('url', 'hash_key', 'owner', 'title', 
                  'photo_thumbnail', 'photo_small_thumbnail', 'liked', 
                  'likes_count', 'plays_count', 'clips_count', 'duration',
                  'score',
                  'new_likes_count', 'new_clips_count', 'membership_status',
                  'created_at', 'updated_at', 'clips', 'users_url')
        read_only_fields = ('id', 'hash_key', 'likes_count',
                            'plays_count', 'clips_count', 'duration', 'score',
                            'created_at', 'updated_at', 'clips')
        
    def get_photo_thumbnail(self, obj):
        """
        Get the absolute URI of the video's photo thumbnail
        """
        return obj.get_photo_thumbnail_url()
    
    def get_photo_small_thumbnail(self, obj):
        """
        Get the absolute URI of the video's small photo thumbnail
        """
        return obj.get_photo_small_thumbnail_url()
    
    def get_liked(self, obj):
        """
        Determine if the current request user liked the video
        """
        user = self.context['request'].user
        
        has_liked = False
        try:
            like_activities = obj.prefetched_activity_object_likes
            has_liked = len(like_activities) > 0
        
        except AttributeError:
            if user.is_authenticated():
                has_liked = Activity.objects.filter(
                    actor_id=user.id, verb='like', object_id=obj.id,
                    object_content_type=ContentType.objects.get_for_model(obj)
                    ).exists()
        
        return has_liked
        
    def get_new_likes_count(self, obj):
        """
        Dummy value to be overwritten in `to_representation`
        """
        return 0 
    
    def get_new_clips_count(self, obj):
        """
        Dummy value to be overwritten in `to_representation`
        """
        return 0
    
    def get_membership_status(self, obj):
        """
        Dummy value to be overwritten in `to_representation`
        """
        return VideoUsers.STATUS_NONE
        
    def to_representation(self, obj):
        """
        List of object instances -> List of dicts of primitive datatypes.
        
        Add the fields: new_likes_count, new_clips_count, membership_status
        and do it all in 1 query
        """
        ret = super(VideoSerializer, self).to_representation(obj)
        
        # check for if we need to override the VideoUsers object stats
        if 'new_likes_count' not in ret:
            return ret
                
        new_clips_count = 0
        new_likes_count = 0
        status = VideoUsers.STATUS_NONE
        
        user = self.context['request'].user
        video_user = None
        try:
            videousers = obj.prefetched_videousers
            if len(videousers) == 1:
                video_user = videousers[0]
        except AttributeError:
            if user.is_authenticated():
                try:
                    video_user = VideoUsers.objects.get(
                        video_id=obj.id, user_id=user.id)
                except VideoUsers.DoesNotExist:
                    pass
        
        if video_user is not None:
            new_clips_count = video_user.new_clips_count
            new_likes_count = video_user.new_likes_count
            status = video_user.status

        ret['new_likes_count'] = new_likes_count
        ret['new_clips_count'] = new_clips_count
        ret['membership_status'] = status
        
        return ret
        

class VideoCreationSerializer(VideoSerializer):
    """
    Serializer to be used for  creating videos with a provided clip and a
    validated list of video users
    """
    lead_clip = ClipSerializer(source='get_lead_clip')
    users = UserNumberSerializer(many=True, required=False)
        
    class Meta:
        model = Video
        fields = ('url', 'hash_key', 'owner', 'title',
                  'photo_thumbnail',  'photo_small_thumbnail', 'lead_clip', 
                  'users', 'liked', 
                  'likes_count', 'plays_count', 'clips_count', 'duration', 
                  'score',
                  'new_likes_count', 'new_clips_count', 'membership_status',
                  'created_at', 'updated_at', 'clips', 'users_url')
        read_only_fields = ('id',  'hash_key', 'photo', 'likes_count',
                            'plays_count', 'clips_count', 'duration', 'score',
                            'created_at', 'updated_at', 'clips')
        extra_kwargs = {'lead_clip': {'write_only': True},
                        'users': {'write_only': True}}
    
    def to_internal_value(self, data):
        """
        Dict of native values <- Dict of primitive datatypes.
        """
        value = super(VideoCreationSerializer, self).to_internal_value(data)
        
        # Convert plain phone numbers array into the format expected by
        # UserNumberSerializer
        phone_numbers = data.getlist('users[][phone_number]', [])
        users_phone_numbers = [{'phone_number': p} for p in phone_numbers]
        value['users'] = users_phone_numbers
                
        # validate the users using logic from ListSerializer.to_internal_value
        errors = []
        user_number_serializer = UserNumberSerializer()
        for user_number in value['users']:
            try:
                validated_user_number = user_number_serializer.run_validation(
                    user_number)
            except serializers.ValidationError as exc:
                errors.append(exc.detail)
                        
        if any(errors):
            raise serializers.ValidationError(errors)
        
        return value
    
    def create(self, validated_data):
        """
        Create a new Video instance
        """
        clip_data = validated_data.pop('get_lead_clip')
        users_data = validated_data.pop('users', [])
        # remove clips from validated data
        validated_data.pop('get_clips')
        
        user = self.context['request'].user
        video = Video.objects.create(owner=user, **validated_data)
        Clip.objects.create(owner=user, video=video, **clip_data)
        
        # get users in UserNumber list serializer
        users = self.fields['users'].create(users_data)
        # add these users as video users
        new_video_users = VideoUsers.objects.add_users_to_video(video, *users)
        new_users = [video_user.user for video_user in new_video_users]
        
        # log creation of all users and send them push notifications
        request = self.context['request']
        for user in new_users:
            activity.send(request.user, verb='invite', 
                          object=user, target=video)
        for video_user in new_video_users:
            video_user.send_invitation_message(request.user)
        
        # finally return created video
        return video
        

class VideoUserSerializer(serializers.ModelSerializer):
    """
    Serializer to be used for getting and updating video users
    """
    
    # cannot use HyperlinkedIdentityField for the url field because it doesn't
    # work with multi-parameter URLs
    url =  serializers.SerializerMethodField()
    
    user = UserPublicSerializer(read_only=True)
            
    class Meta:
        model = VideoUsers
        fields = ('url', 'user', 'status', 'created_at', 'updated_at',)
        read_only_fields = ('created_at', 'updated_at',)
        
    def get_url(self, obj):
        """
        Build out the absolute URI of the clip object including the host and
        protocol.
        """
        request = self.context['request']
        return request.build_absolute_uri(obj.get_absolute_url())


class VideoUsersCreationSerializer(serializers.Serializer):
    """
    Serializer class for video user creation which validates the `users`
    to-many fields.
    """
    users = UserNumberSerializer(many=True)
    
    def create(self, validated_data):
        """
        Get the current video instance and attach associated user list
        given a dictionary of deserialized field values.
        """
        # get video
        hash_key = self.context['view'].kwargs.get('hash_key')
        video = Video.objects.get(hash_key=hash_key)
        
        # get users in UserNumber list serializer
        users = self.fields['users'].create(self.data['users'])
        # add these users as video users
        new_video_users = VideoUsers.objects.add_users_to_video(video, *users)
        new_users = [video_user.user for video_user in new_video_users]
                
        # log creation of all users and send them push notifications
        request = self.context['request']
        for user in new_users:
            activity.send(request.user, verb='invite', 
                          object=user, target=video)
        for video_user in new_video_users:
            video_user.send_invitation_message(request.user)
                
        # save video to update its updated_at property
        video.save()
        return video


class ClipMinimalSerializer(ClipSerializer):
    """
    Serializer to be used for providing minimal information about a Clip
    necessary for showing it in the activity stream
    """
            
    class Meta:
        model = Clip
        fields = ('id', 'order', 'mp4', 'photo_thumbnail', 
                  'duration', 'updated_at')
        read_only_fields = ('id', 'order', 'mp4', 'duration', 'updated_at')
                        

class VideoMinimalSerializer(VideoSerializer):
    """
    Serializer to be used for providing minimal information about a Video
    necessary for showing it in the activity stream
    """
            
    class Meta:
        model = Video
        fields = ('hash_key', 'title', 'photo_small_thumbnail', 'updated_at',)
        read_only_fields = ('hash_key', 'title', 'updated_at',)

