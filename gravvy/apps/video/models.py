import uuid
import hashlib
import random

from django.db import models
from django.utils import timezone, six
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from imagekit.models import ImageSpecField
from imagekit.processors import SmartResize, Adjust, Transpose

from gravvy.utils import get_upload_path
from gravvy.apps.account.models import User
from gravvy.apps.push.utils import (
    send_sms_message, send_bulk_sms_message, send_push_message, 
    send_bulk_push_message)
from gravvy.apps.activity.models import Activity

# Create your models here.

# ---------------------------------------------------------------------------- #
# CONSTANTS
# ---------------------------------------------------------------------------- #
VIDEO_HASH_LENGTH = 10
VIDEO_USERS_HASH_LENGTH = 10
# Assume 153 characters max length but account for many unicode characters
VIDEO_TITLE_LENGTH = 50


# ---------------------------------------------------------------------------- #
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------- #

def get_video_photo_path(instance, filename):
    """
    Upload path for video cover image file
    
    Args:
        instance: video model instance where file is being attached
        filename: filename that was originally given to the file
    
    Returns: 
        Unique filepath for given file, that's a subpath of `img/c/`
    """
    return get_upload_path(instance, filename, 'img/v/')


def get_clip_photo_path(instance, filename):
    """
    Upload path for video clips cover image file
    
    Args:
        instance: Clip model instance where file is being attached
        filename: filename that was originally given to the file
    
    Returns: 
        Unique filepath for given file, that's a subpath of `img/c/`
    """
    return get_upload_path(instance, filename, 'img/c/')


def get_clip_mp4_path(instance, filename):
    """
    Upload path for video clip mp4 file
    
    Args:
        instance: Clip model instance where file is being attached
        filename: filename that was originally given to the file
    
    Returns: 
        Unique filepath for given file, that's a subpath of `vid/c/`
    """
    return get_upload_path(instance, filename, 'vid/c/')


def video_push_dictionary(video, user, message,
                          action_type=settings.PUSH_ACTION_TYPE_DEFAULT,
                          object_identifier=None):
    """
    Generate the Push notification object's extra parameters to be consumed by 
    the ios app when .
        
    Args:
        video: Video that push notification is about
        user: user performing the push notification action
        message: Message to be used when app is in foreground upon push arrival
        action_type: push action type to be parsed by device
        object_identifier: identifier of action type's related object
        
    Returns:
        dictionary of extra parameters
    """
    extra = {} # must be an empty dictionary but not None
    if video:
        extra[settings.PUSH_VIDEO_HASH_KEY_KEY] = video.hash_key
    
    if user:
        extra[settings.PUSH_VIDEO_USER_PHONE_NUMBER_KEY] = user.phone_number.as_e164
        extra[settings.PUSH_VIDEO_USER_FULL_NAME_KEY] = user.full_name
        
    if message:    
        extra[settings.PUSH_VIDEO_MESSAGE_KEY] = message
    
    extra[settings.PUSH_ACTION_TYPE_KEY] = action_type
    
    if object_identifier:
        extra[settings.PUSH_ACTION_OBJECT_IDENTIFIER_KEY] = object_identifier
    
    return extra


# ---------------------------------------------------------------------------- #
# MODEL CLASSES
# ---------------------------------------------------------------------------- #

class Video(models.Model):
    """
    Video stream class which is the container class of the linked video clips.
    """
    owner = models.ForeignKey(
        User, related_name="owned_videos", verbose_name=_('owner'),
        help_text=_("Video's primary owner that can modify its settings"))
    
    hash_key = models.CharField(
        _('unique hash'), max_length=20, unique=True,
        help_text=_("unique identifier of video object"))
    
    title = models.CharField(
        _('title'), max_length=200, blank=True, help_text=_('video title'))
    
    description = models.CharField(
        _('description'), max_length=1000, blank=True, 
        help_text=_('video details'))
    
    # no need to add null=True as that doesnt make sense in the context of M2M
    users = models.ManyToManyField(
        User, related_name="videos", verbose_name=_('users'), blank=True,
        through='VideoUsers', help_text=_("Users associated with video"))
    
    activity_targets = GenericRelation(
        Activity, related_query_name='target_videos',
        content_type_field='target_content_type',
        object_id_field='target_id',
        help_text=_("Activities which have this video as the target"))
    
    activity_objects = GenericRelation(
        Activity, related_query_name='object_videos',
        content_type_field='object_content_type',
        object_id_field='object_id',
        help_text=_("Activities which have this video as the object"))
    
    # Copy of leading clip's preview image so as to not make database queries
    # to get this for every video. This really helps performance.
    photo =  models.ImageField(
        _('photo'), upload_to=get_video_photo_path,
        help_text=_("copy of preview image of video's first clip from its "
                    "collection of associated clips."))
    
    # imagekit spec for thumbnail-sized image.
    # The Transpose processor will use the metadata in the image and rotate by 
    # the specified amount. This ensures the image will be the right orientation
    # We put this processor first as subsequent processors will strip the
    # metadata from the image.
    photo_thumbnail = ImageSpecField(
        source='photo',
        processors=[Transpose(Transpose.AUTO),
                    SmartResize(width=settings.VIDEO_PHOTO_THUMBNAIL_SIZE, 
                                height=settings.VIDEO_PHOTO_THUMBNAIL_SIZE),
                    Adjust(contrast = 1.2, sharpness=1.1)],
        format='JPEG',
        options={'quality':90})
    
    # imagekit spec for small/activity stream thumbnail-sized image
    photo_small_thumbnail = ImageSpecField(
        source='photo',
        processors=[Transpose(Transpose.AUTO),
                    SmartResize(
                width=settings.VIDEO_PHOTO_ACTIVITY_THUMBNAIL_SIZE, 
                height=settings.VIDEO_PHOTO_ACTIVITY_THUMBNAIL_SIZE),
                    Adjust(contrast = 1.2, sharpness=1.1)],
        format='JPEG',
        options={'quality':90})
    
    likes_count = models.IntegerField(
        _('likes count'), default=0, validators=[MinValueValidator(0)],
        help_text=_("Number of likes"))
    
    plays_count = models.IntegerField(
        _('plays count'), default=0, validators=[MinValueValidator(0)],
        help_text=_("Number of plays"))
    
    clips_count = models.IntegerField(
        _('clips count'), default=0, validators=[MinValueValidator(0)],
        help_text=_("Number of clips"))
    
    duration = models.FloatField(
        _('total duration'), default=0.0,
        help_text=_("total duration of all clip mp4s, in seconds."))
    
    created_at = models.DateTimeField(
        _('date created'), default=timezone.now, 
        help_text=_('creation date/time'))
    
    updated_at = models.DateTimeField(_('last update date/time'), auto_now=True)
    
    # this is used for tracking photo changes
    # ref: http://stackoverflow.com/a/1793323
    __original_photo = None
    
    class Meta:
        ordering = ['-updated_at'] 
        verbose_name = _('video')
        verbose_name_plural = _('videos')
        
    def __init__(self, *args, **kwargs):
        super(Video, self).__init__(*args, **kwargs)
        self.__original_photo = self.photo
        
    def __unicode__(self):
        return '%s (%s)' % (self.title, self.hash_key)
    
    def __str__(self):
        """
        Fixes the annoying exception: 
            DjangoUnicodeDecodeError: 'ascii' codec can't decode byte
        """
        return self.hash_key
    
    def get_absolute_url(self):
        return reverse('video-detail', kwargs={'hash_key':self.hash_key})
    
    def get_title(self):
        """
        Get a representative title of a video
        """
        title = self.title
        if title == '':
            title = 'a video'
            
        else:
            if len(title) > VIDEO_TITLE_LENGTH:
                # need to truncate but account for the ellipsis
                # ref: http://stackoverflow.com/a/1820949
                encoded_title = title.encode('utf-8')
                max_title_length = VIDEO_TITLE_LENGTH-3
                truncated_title = (
                    encoded_title[:max_title_length] + 
                    (encoded_title[max_title_length:] and '...'))
                title =  truncated_title.decode(encoding='utf-8',
                                                errors='ignore')
            title = '"%s"' % (title,)
            
        return title
    
    def get_photo_thumbnail_url(self):
        """
        get url of photo's thumbnail. If there isn't a photo_thumbnail then
        return an empty string
        """
        return self.photo_thumbnail.url if self.photo_thumbnail else ''
    
    def get_photo_small_thumbnail_url(self):
        """
        get url of photo's small thumbnail. If there isn't a 
        photo_small_thumbnail then return an empty string
        """
        return (self.photo_small_thumbnail.url 
                if self.photo_small_thumbnail else '')
    
    @property
    def score(self):
        """
        Score song using an algorithm based on the ranking performed by
        Hacker News where video is scored using the formula:
            Score = (P)/(T+2)^G
            where,
            P = Points of an item
            T = time since creation (in hours)
            G = Gravity
            
        Reference: 
            http://amix.dk/blog/post/19574
        """
        # determine points of an item where plays and likes are weighted
        points = (settings.VIDEO_PLAYS_COUNT_WEIGHT*self.plays_count + 
                  settings.VIDEO_LIKES_COUNT_WEIGHT*self.likes_count)
        
        # determine hours since creation
        time_since_created = timezone.now() - self.created_at
        hours = time_since_created.total_seconds()/3600.0
        
        rank_score = points / ((hours + 2.0)**settings.VIDEO_SCORE_GRAVITY)
        return rank_score
    
    def delete_photo_files(self, instance):
        """
        Delete a video's photo files in storage
            * First delete the clip's ImageCacheFiles on storage. The reason 
              this must happen first is that deleting source file deletes the 
              associated ImageCacheFile references but not the actual 
              ImageCacheFiles in storage.
            * Next delete source file (this also performs a delete on the 
              storage backend)
                
        Args:   
            instance: Clip object instance to have files deleted
        
        Returns:      
            None 
        """
        # get photo_thumbnail location and delete it
        instance.photo_thumbnail.storage.delete(instance.photo_thumbnail.name)
        # delete photo
        instance.photo.delete()
        
    def get_lead_clip(self):
        """
        Get first clip in the video stream.
        
        Returns:
            Clip instance or None
        """
        clips = list(self.clips.all().select_related(
                'owner').order_by('order')[:1])
        return clips[0] if len(clips) else None
    
    def get_clips(self):
        """
        Get all clips of the video stream, but optimize for db queries
        by selecting owner as well
        """
        return getattr(self, 'prefetched_clips', 
                       self.clips.select_related('owner'))
    
    def generate_hash_key(self):
        """
        Generate unique string to be used as hash key for Video object
        
        Returns:
            Unique hash key
        """
        # Generate the hash key
        hash_key = unicode(uuid.uuid4()).replace('-','')[:VIDEO_HASH_LENGTH]
        
        # Confirm it's unique
        if Video.objects.filter(hash_key=hash_key).exists():
            # hash key isn't unique so append owner id to it
            hash_key = hash_key+str(self.owner_id)
        return hash_key
    
    def refresh_photo(self):
        """
        Update cached photo of leading clip. This should only be called
        when the leading clip is changed.
        """
        lead_clip = self.get_lead_clip()
        self.photo = lead_clip.photo if lead_clip else None
        self.save()
        
    def refresh_clip_stats(self):
        """
        Refresh clips_count and duration
        """
        clips = self.clips.all()
        self.clips_count = clips.count()
        self.duration = clips.aggregate(models.Sum('duration'))['duration__sum']
        self.save()
        
    def refresh_likes_count(self):
        """
        Refresh number of likes on video by querying Activity model
        """
        self.likes_count = Activity.objects.filter(
            verb='like', object_id=self.id,
            object_content_type=ContentType.objects.get_for_model(self)).count()
        self.save()
            
    def save(self, *args, **kwargs):
        """
        On instance creation, generate hash key and set owner as an associated
        user if this isn't already the case.
        On instance save, if photo has changed, delete old photo's files
                
        Args:   
            *args: all positional arguments
            **kwargs: all keyword arguments

        Returns:
            None 
        """
        # determine if this is a create/update operation,i.e. if this video is
        # being saved for the first time or not
        new_video = False
        if self.pk is None:
            new_video = True
            # generate a hash key now
            self.hash_key = self.generate_hash_key()
            
        if self.__original_photo and self.photo != self.__original_photo:
            # photo has changed and this isn't the first photo upload, so
            # delete old files.
            orig = Video.objects.get(pk=self.pk)
            self.delete_photo_files(orig)
        
        super(Video, self).save(*args, **kwargs)
        
        # update the image file tracking properties
        self.__original_photo = self.photo

        # set owner as an associated user if this isn't already the case
        if new_video:
            VideoUsers.objects.add_users_to_video(self, self.owner)
    
    def delete(self, *args, **kwargs):
        """
        Default model delete() doesn't call delete() on related Clip and
        Activity objects or delete instance's media files. So do that here to 
        ensure necessary media files are cleaned up.
        
        Args:
            *args: all positional arguments
            **kwargs: all keyword arguments

        Returns:
            None 
        """
        # if there were image files, delete those
        if self.photo:
            self.delete_photo_files(self)
            
        # cleanup clips' media files
        for clip in self.clips.all():
            clip.delete(refresh_video=False)
            
        # cleanup related Activities
        content_type = ContentType.objects.get_for_model(self)
        Activity.objects.filter(
            models.Q(object_id=self.id, object_content_type=content_type) |
            models.Q(target_id=self.id, target_content_type=content_type)
            ).delete()
        
        super(Video, self).delete(*args, **kwargs)
        
    def send_new_like_notification(self, sender):
        """
        Send notification saying the video has been liked.
        The notification goes out to all video clip creators with the app 
        installed
        
        Args:
            sender: User who liked the video
        """
        video_title = self.get_title()
        sender_name = sender.get_short_name()
        
        # Create content for alert shown when app is in foreground
        extra_message = "Liked video"
        push_extra = video_push_dictionary(
            self, sender, extra_message, settings.PUSH_ACTION_TYPE_LIKED)
        
        # Setup content for alert shown when app is in background/inactive
        push_message = ('%s liked %s' % (sender_name, video_title))
        
        # clips_users get loud push notifications
        clips = self.clips.all().select_related('owner')
        clips_users = [clip.owner for clip in clips 
                       if clip.owner.is_active == True and clip.owner != sender]
        send_bulk_push_message(clips_users, push_message, extra=push_extra)
        
        # all other video users get silent notifications
        excluded_user_ids = [user.id for user in clips_users]
        excluded_user_ids.append(sender.id)
        users = self.users.filter(is_active=True).exclude(
            id__in=excluded_user_ids)
        send_bulk_push_message(users, None, extra=push_extra)
            

class Clip(models.Model):
    """
    Representation of each Video Clip, which is what makes up each segment of a
    video.
    
    Each video is made up of ordered clips played in sequence to simulate a
    continuous video stream.
    """
    owner = models.ForeignKey(
        User, related_name="owned_clips", verbose_name=_('owner'),
        help_text=_('clip uploader'))
    
    video = models.ForeignKey(
        Video, related_name="clips", verbose_name=_('video'),
        help_text=_('associated video'))
    
    order = models.SmallIntegerField(
        _('clip order'), validators=[MinValueValidator(0)],
        help_text=_("0-indexed order in video; 0 means this is the first clip"))
        
    mp4 = models.FileField(
        _('mp4'), upload_to=get_clip_mp4_path,
        help_text=_("clip's mp4 file"))
    
    photo =  models.ImageField(
        _('photo'), upload_to=get_clip_photo_path,
        help_text=_("image of a frame in mp4 that serves as a "
                    "preview/fallback image"))
    
    # imagekit spec for thumbnail-sized image.
    photo_thumbnail = ImageSpecField(
        source='photo',
        processors=[Transpose(Transpose.AUTO),
                    SmartResize(width=settings.VIDEO_PHOTO_THUMBNAIL_SIZE, 
                                height=settings.VIDEO_PHOTO_THUMBNAIL_SIZE),
                    Adjust(contrast = 1.2, sharpness=1.1)],
        format='JPEG',
        options={'quality':90})
    
    duration = models.FloatField(
        _('clip duration'), default=0.0,
        help_text=_("duration of clip mp4, in seconds."))
    
    created_at = models.DateTimeField(
        _('date created'), default=timezone.now, 
        help_text=_('creation date/time'))
    
    updated_at = models.DateTimeField(_('last update date/time'), auto_now=True)
    
    class Meta:
        verbose_name = _('video clip')
        verbose_name_plural = _('video clips')
        ordering = ('order',)
        
    def __unicode__(self):
        return u'owner:%s video:%s' % (self.owner, self.video)
    
    def get_absolute_url(self):
        return reverse('video-clip-detail', 
                       kwargs={'hash_key':self.video.hash_key,
                               'pk':self.pk})
    
    def get_photo_thumbnail_url(self):
        """
        get url of photo's thumbnail. If there isn't a photo_thumbnail then
        return an empty string
        """
        return self.photo_thumbnail.url if self.photo_thumbnail else ''
    
    def delete_photo_files(self, instance):
        """
        Delete a clip's photo files in storage
            * First delete the clip's ImageCacheFiles on storage. The reason 
              this must happen first is that deleting source file deletes the 
              associated ImageCacheFile references but not the actual 
              ImageCacheFiles in storage.
            * Next delete source file (this also performs a delete on the 
              storage backend)
                
        Args:   
            instance: Clip object instance to have files deleted
        
        Returns:      
            None 
        """
        # get photo_thumbnail location and delete it
        instance.photo_thumbnail.storage.delete(instance.photo_thumbnail.name)
        # delete photo
        instance.photo.delete()

    def save(self, *args, **kwargs):
        """
        On instance creation, specify clip order and update video stats
                
        Args:   
            *args: all positional arguments
            **kwargs: all keyword arguments

        Returns:
            None 
        """
        new_clip = False
        if self.pk is None:
            new_clip = True
            qs = self.__class__.objects.filter(
                video=self.video).order_by('-order')
            # if a new clip is being created, it's order will be next up in the
            # video
            try:
                self.order = qs[0].order + 1
            except IndexError:
                # but if this new clip is also the first clip associated with
                # the video start it off with a 0-based index. 
                self.order = 0
        
        super(Clip, self).save(*args, **kwargs)
        
        # if this was the first clip of the video, the video need to refresh its
        # cached copy of the photo
        if self.order == 0:
            self.video.refresh_photo()
            
        # if this is a new clip update clip stats and inform video users
        if new_clip:
            # update associated video user's status
            video_user = VideoUsers.objects.get(
                video_id=self.video.id, user_id=self.owner.id)
            video_user.added_clip()
            self.video.refresh_clip_stats()
            self.send_new_clip_notification()
        
    def delete(self, *args, **kwargs):
        """
        Default model delete() doesn't delete files on storage, so force that to
        happen.
        If this is the associated video's lead clip, have the photo update its
        lead clip image after the delete
        
        Args:
            *args: all positional arguments
            **kwargs: all keyword arguments

        Returns:
            None 
        """
        # if there were image files, delete those
        if self.photo:
            self.delete_photo_files(self)
        # if there was an mp4 file, delete that
        if self.mp4:
            self.mp4.delete()
        
        # check if this is the associated video's lead clip
        lead_clip = self.__class__.objects.filter(
            video=self.video).order_by('order')[0]
        is_lead_clip = self.pk == lead_clip.pk
        # cache the video, owner, and clip id for use after delete
        video = self.video
        owner = self.owner
        clip_pk = self.pk
        
        # cleanup related Activities
        content_type = ContentType.objects.get_for_model(self)
        Activity.objects.filter(
            models.Q(object_id=self.id, object_content_type=content_type) |
            models.Q(target_id=self.id, target_content_type=content_type)
            ).delete()
        
        refresh_video = kwargs.pop('refresh_video', True)
        super(Clip, self).delete(*args, **kwargs)
        
        if refresh_video:
            video.refresh_clip_stats()
            if is_lead_clip:
                video.refresh_photo()
        
        self.send_deleted_clip_notification(video, owner, clip_pk)
                
    def send_new_clip_notification(self):
        """
        Send notification saying a new clip has been added to the video.
        The notification goes out to all video users with the app installed,
        i.e. active video users, except the clip owner.
        """
        video_title = self.video.get_title()
        clip_owner_name = self.owner.get_short_name()
        
        # Create content for alert shown when app is in foreground
        extra_message = "Added new clip"
        push_extra = video_push_dictionary(
            self.video, self.owner, extra_message,
            settings.PUSH_ACTION_TYPE_ADDED_CLIP, self.pk)
                
        # Setup content for alert shown when app is in background/inactive
        push_message = ('%s @ %s:\nAdded new clip'
                        % (clip_owner_name, video_title))
        
        users = self.video.users.filter(is_active=True).exclude(
            pk=self.owner.pk)
        send_bulk_push_message(users, push_message, extra=push_extra)
    
    def send_deleted_clip_notification(self, video, owner, clip_pk):
        """
        Send notification saying this clip is now deleted. The notification
        goes to all video users with the app installed, i.e. active video
        users, except clip owner
        
        Args:
            video: Clip's associated vide
            owner: Clips's owner
            clip_pk: Primary key of the now deleted clip
        """
        push_extra = video_push_dictionary(
            video, owner, None, settings.PUSH_ACTION_TYPE_DELETED_CLIP, 
            clip_pk)
        users = video.users.filter(is_active=True).exclude(pk=owner.pk)
        send_bulk_push_message(users, None, extra=push_extra)


class VideoUsersManager(models.Manager):
    """
    Custom Model Manager for VideoUsers class.
    
    We are using VideoUsers as a through-table for the many-to-many relationship
    between videos and users. This means we lose the default django convenience 
    methods defined on M2M fields, `add()` and `remove()`.
    
    This Manager gives us back versions of those methods
    """
    
    def add_users_to_video(self, video, *users):
        """
        Associate users with a given video's collection of users
        
        Args:
            video: video to associate users with
            users: 0 or more user objects to add to video.users
            
        Returns:
            A list of the created VideoUser objects
        """
        # we wont save the associations individually, so collect the VideoUsers
        # association objects in a list to be bulk saved later
        associations_to_create = []
        
        users = list(users)
        users_ids = [u.id for u in users]
        
        # Get users that are already added to the video
        users_already_added = video.users.filter(id__in=users_ids)
        
        # Get users to add by (users - users_already_added)
        users_to_add = [u for u in users if u not in users_already_added]
        
        for user in users_to_add:
            association = self.model(video=video, user=user)
            association.hash_key = association.generate_hash_key()
            associations_to_create.append(association)
        
        # now bulk create all these associations
        self.bulk_create(associations_to_create)
        return associations_to_create
    
    def remove_users_from_video(self, video, *users):
        """
        Dissociate users with a given video's collection of users
        
        Args:
            video: video to dissociate users with
            users: 0 or more user objects to remove from video.users
            
        Returns:
            None
        """
        users = list(users)
        associations = self.filter(video=video, user__in=users)
        associations.delete()
        

class VideoUsers(models.Model):
    """
    Table used for defining the many-to-many relationship between videos and
    users.
    
    It has additional fields for representing user settings and details relating
    to a video. One such field is the hash_key to be used when sending an SMS
    to a user about a video they've been added to.
    """
    video = models.ForeignKey(Video) # The 1 foreign key to source model
    user = models.ForeignKey(User)   # The 1 foreign key to target model
    
    hash_key = models.CharField(
        _('unique hash'), max_length=20, unique=True,
        help_text=_("unique identifier of video user object"))
    
    # User's interaction status with the video. This indicates
    # if user has just been invited and user has viewed video since invitation
    STATUS_NONE = 0
    STATUS_INVITED = 1
    STATUS_VIEWED = 2
    STATUS_CONTRIBUTED = 3
    INTERACTION_STATUS_CHOICES = (
        (STATUS_INVITED, 'Invited'),
        (STATUS_VIEWED, 'Viewed post-invite'),
        (STATUS_CONTRIBUTED, 'Uploaded a clip'),
        )
    status = models.IntegerField(
        _('Video interaction status'), 
        choices=INTERACTION_STATUS_CHOICES, default=STATUS_INVITED) 
    
    new_likes_count = models.IntegerField(
        _('New likes count'), default=0, validators=[MinValueValidator(0)],
        help_text=_("count of new video likes that haven't been acknowledged "
                    "by video user"))
    
    new_clips_count = models.IntegerField(
        _('New clips count'), default=0, validators=[MinValueValidator(0)],
        help_text=_("count of new video clips that haven't been acknowledged "
                    "by video user"))
    
    created_at = models.DateTimeField(
        _('date created'), default=timezone.now,
        help_text=_("Video user creation date/time"))
    
    # last update date to be used by client apps for sync purposes.
    # ref: http://stackoverflow.com/a/5052208
    updated_at = models.DateTimeField(_('last update date/time'), 
                                      auto_now=True)
    
    objects = VideoUsersManager()
        
    class Meta:
        unique_together = ('video', 'user')
        verbose_name = _('video user')
        verbose_name_plural = _('video users')
        ordering = ('-created_at',)
                
    def __unicode__(self):
        return u'user:%s video:%s' % (str(self.user), str(self.video))
    
    def get_absolute_url(self):
        return reverse('video-user-detail', 
                       kwargs={'hash_key':self.video.hash_key,
                               'phone_number':self.user.phone_number})
    
    def generate_hash_key(self):
        """
        Generate unique string to be used as hash key for current VideoUser
        object.
        """
        # Generate the hash key
        salt = hashlib.sha1(six.text_type(random.random()).encode(
                'ascii')).hexdigest()[:5]
        salt = salt.encode('ascii')
        phone_number = self.user.phone_number.as_e164.encode('utf-8')
        video_hash = self.video.hash_key.encode('utf-8')
        hash_key = hashlib.sha1(salt+phone_number+video_hash).hexdigest()[
            :VIDEO_USERS_HASH_LENGTH]
        
        # Confirm hash key is unique. If it isn't append user id and video id
        # to it.
        #if VideoUsers.objects.filter(hash_key=hash_key).exists():
        #    hash_key = hash_key+str(self.user_id)+str(self.video_id)
        
        return hash_key
    
    def save(self, *args, **kwargs):
        """
        On instance creation, generate object's hash key.
                
        Args:   
            *args: all positional arguments
            **kwargs: all keyword arguments

        Returns:
            None 
        """
        
        if self.pk is None:
            # generate a hash key now
            self.hash_key = self.generate_hash_key()
            
        super(VideoUsers, self).save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        """
        On object delete, update parent video to indicate change in related
        user entity
        
        Args:
            *args: all positional arguments
            **kwargs: all keyword arguments

        Returns:
            None 
        """
        # cache video and user for after instance deletion.
        video = self.video 
        user = self.user
        super(VideoUsers, self).delete(*args, **kwargs)
        
        # delete these user's clips in the video
        owned_clips = video.clips.filter(owner_id=user.id)
        for clip in owned_clips:
            clip.delete()
        
        video.save() # this refreshes video's updated_at time
        self.send_removed_user_notification(video, user)
        
    def added_clip(self):
        """
        update status to indicate added a clip
        """
        if self.status < self.STATUS_CONTRIBUTED:
            self.status = self.STATUS_CONTRIBUTED
            self.save()
        
    def send_invitation_message(self, sender):
        """
        Send message informing user that they've been invited to a video.
        If user's account is active, attempt sending a push notification.
        Otherwise send user an sms
        
        Args:
            sender: User inviting the user to a video
        """
        sender_name = sender.get_short_name()
        video_title = self.video.get_title()
        
        if self.user.is_active == True:
            # user is active, so send a push notification
            # Create content for alert shown when app is in foreground
            extra_message = 'Invited you to video'
            push_extra = video_push_dictionary(
                self.video, sender, extra_message,
                settings.PUSH_ACTION_TYPE_INVITED_USER_TO_VIDEO)
             
            # Setup content for alert shown when app is in background/inactive
            push_message = ('%s has invited you to %s' 
                            % (sender_name, video_title))
            send_push_message(self.user, push_message, extra=push_extra)
            
        else:
            # user is inactive, so send an sms
            video_url = self.video_web_url()
            message = ('%s has shared %s with you at %s'
                       % (sender_name, video_title, video_url))
            send_sms_message(self.user, message)
    
    def video_web_url(self):
        """
        Generate the video URL to be sent out to users via SMS so they can 
        access a given event via their web browsers
        """
        video_url_path = reverse('web-video-detail', 
                                 kwargs={'hash_key':self.video.hash_key})
        url = "{base}{path}".format(base=settings.HTTP_DOMAIN, 
                                    path=video_url_path)
        return url
    
    def send_added_user_notification(self):
        """
        Send notification saying user has been added as video user.
        The notification goes to all video users with the app installed
        """        
        # Create content for alert shown when app is in foreground
        push_extra = video_push_dictionary(
            self.video, self.video.owner, None,
            settings.PUSH_ACTION_TYPE_ADDED_USER, 
            self.user.phone_number.as_e164)        
        users = self.video.users.filter(is_active=True)
        send_bulk_push_message(users, None, extra=push_extra)
        
    def send_removed_user_notification(self, video, user):
        """
        Send notification saying user has been removed as video user.
        The notification goes to all video users with the app installed, i.e.
        active event members.
        
        Args:
            video: video that user was removed from
            user: video user that was removed from video
        """
        push_extra = video_push_dictionary(
            video, video.owner, None, settings.PUSH_ACTION_TYPE_REMOVED_USER, 
            user.phone_number.as_e164)
        users = video.users.filter(is_active=True)
        users = list(users)
        users.append(user)
        send_bulk_push_message(users, None, extra=push_extra)
