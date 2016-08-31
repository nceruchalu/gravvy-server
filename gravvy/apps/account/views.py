from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Prefetch
from django.contrib.contenttypes.models import ContentType

from rest_framework import generics, status, permissions, parsers, renderers
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from gravvy.apps.account.models import  User, AuthToken, RegistrationProfile
from gravvy.apps.account.permissions import IsOwnerOrReadOnly, IsDetailOwner
from gravvy.apps.account.authentication import ExpiringTokenAuthentication
from gravvy.apps.account.serializers import (
    UserPublicSerializer, UserPrivateSerializer, UserCreationSerializer,
    AuthTokenSerializer, ActivateAccountSerializer)

from gravvy.apps.video.models import Video, VideoUsers, Clip
from gravvy.apps.video.serializers import VideoSerializer

from gravvy.apps.activity.models import Activity
from gravvy.apps.activity.serializers import ActivitySerializer
from gravvy.apps.activity.pagination import ActivityCursorPagination

# Create your views here.

# -----------------------------------------------------------------------------
# USERS LIST
# -----------------------------------------------------------------------------

class UserList(generics.CreateAPIView):
    """
    Create a new user. 
    
    ## Reading
    You can't read using this endpoint. While it would seem nice for this API 
    endpoint to list all users you can imagine why this is a user privacy issue.
    
    
    ## Publishing
    ### Permissions
    * Anyone can create using this endpoint.
    
    ### Fields
    Parameter      | Description                                 | Type
    -------------- | ------------------------------------------- | ---------- 
    `phone_number` | phone number for the new user. **Required** | _string_
    `password`     | password for the new user. **Required**     | _string_
    
    ### Response
    If create is successful, a limited scope user object, otherwise an error 
    message. 
    The limited scope user object has the following fields:
    
    Name           | Description                              | Type
    -------------- | ---------------------------------------- | ---------- 
    `url`          | URL of new user object                   | _string_
    `id`           | The ID of the newly created user         | _integer_
    `phone_number` | phone number as provided during creation | _string_
    
    
    ## Deleting
    You can't delete using this endpoint
    
    
    ## Updating
    You can't update using this endpoint
    
    
    ## Endpoints
    Name                             | Description                       
    -------------------------------- | ----------------------------------------
    [`/users/<phone number>/`](+18005551234/) | Get/Update a specific user's details
    [`/users/<phone number>/videos/`](+18005551234/videos/) | Get a user's associated videos

    ##
    """
    permission_classes = (permissions.AllowAny,)
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        """
        a POST request implies a user creation so return the serializer for
        user creation. 
        All other possible requests will be GET so use the privacy-respecting
        user serializer
        """
        if self.request.method == "POST":
            return UserCreationSerializer
        else: 
            return UserPublicSerializer


# -----------------------------------------------------------------------------
# USER'S DETAILS AND ASSOCIATED LISTS
# -----------------------------------------------------------------------------

class UserDetail(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a user instance
    
    ## Reading
    ### Permissions
    * Anyone can read this endpoint.
    * Authenticated users reading their own user instance get additional private
      data.
    
    ### Fields
    Reading this endpoint returns a user object containing the public user data.
    An authenticated user reading their own user also gets to see the private
    user data.
    
    Name               | Description                          | Type
    ------------------ | ------------------------------------ | ---------- 
    `url`              | URL of user object                   | _string_
    `id`               | ID of user                           | _integer_
    `phone_number`     | phone number of user object          | _string_
    `full_name`        | full name of user object             | _string_
    `avatar_thumbnail` | URL of user's thumbnail-sized avatar | _string_
    `updated_at`       | last modified date of user object    | _date/time_
    `videos_url` | URL of user's videos sub-collection. **_private_**. | _string_
    
    
    ## Publishing
    You can't create using this endpoint
    
    
    ## Deleting
    You can't delete using this endpoint
    
    
    ## Updating
    Submitting an avatar requires capturing a photo via file upload as 
    **multipart/form-data** then using the `avatar` parameter. 
    
    Note that the request method must still be a PUT/PATCH
    
    ### Permissions
    * Only authenticated users can write to this endpoint.
    * Authenticated users can only update their own user instance.
    
    ### Fields
    Parameter    | Description                    | Type
    ------------ | ------------------------------ | ----------
    `full_name`  | new first name for the user    | _string_
    `avatar`     | new avatar image for the user. This will be scaled to generate `avatar_thumbnail` | _string_
    
    ### Response
    If update is successful, a user object containing public and private data, 
    otherwise an error message.
        
    
    ## Endpoints
    Name                    | Description                       
    ----------------------- | ----------------------------------------
    [`videos`](videos/)     | All the videos this user is associated with
       
    ##
    """
    parser_classes = (parsers.JSONParser, parsers.MultiPartParser,)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    queryset = User.objects.all()
    
    # lookup by 'phone_number' not the 'pk' 
    lookup_field = 'phone_number'
    lookup_url_kwarg = 'phone_number'

    def get_serializer_class(self):
        """
        You only get to see private data if you request details of yourself.
        Otherwise you get to see a limited view of another user's details
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup = self.kwargs[lookup_url_kwarg]
        
        if (self.request.user.is_authenticated() and 
            self.request.user.phone_number == lookup):
            serializer_class = UserPrivateSerializer
        else:
            serializer_class = UserPublicSerializer
        
        return serializer_class
 

class UserVideoList(generics.ListAPIView):
    """
    List all videos associated with a user
    
    ## Reading
    ### Permissions
    * Only authenticated users viewing their own `videos` sub-collection can 
      read this endpoint.
    
    ### Fields
    Reading this endpoint returns a list of 
    [Video objects](../../../videos/hash-key/)
        
    
    ## Publishing
    You can't create using this endpoint
    
    
    ## Deleting
    You can't delete using this endpoint
    
    
    ## Updating
    You can't update using this endpoint
   
    """
    permission_classes = (permissions.IsAuthenticated, IsDetailOwner,)
    serializer_class = VideoSerializer
    # IsDetailOwner permission expects to use the lookup field and url kwarg 
    # to get the object
    lookup_field = 'phone_number'
    lookup_url_kwarg = 'phone_number'
    
    def get_queryset(self):
        """
        This view should return a list of all videos for the user as determined
        by the lookup parameters of the view.
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup = self.kwargs.get(lookup_url_kwarg, None)
        
        if lookup is not None:
            prefetch_videousers = Prefetch(
                'videousers_set', 
                queryset=VideoUsers.objects.filter(user__phone_number=lookup),
                to_attr='prefetched_videousers')
            
            prefetch_clips = Prefetch(
                'clips', 
                queryset=Clip.objects.select_related('owner'),
                to_attr='prefetched_clips')
            
            prefetch_activity_object_likes = Prefetch(
                'activity_objects',
                queryset=Activity.objects.filter(actor__phone_number=lookup, 
                                                 verb='like'),
                to_attr='prefetched_activity_object_likes'
                )

            return Video.objects.filter(
                Q(users__phone_number__in=[lookup]) | 
                Q(owner__phone_number=lookup)).select_related(
                'owner').prefetch_related(
                    prefetch_videousers, prefetch_clips,
                    prefetch_activity_object_likes).distinct()
        return Video.objects.none()


# -----------------------------------------------------------------------------
# AUTHENTICATED USER'S DETAILS AND ASSOCIATED LISTS
# -----------------------------------------------------------------------------

class AuthenticatedUserDetail(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the authenticated user
    
    ## Reading
    ### Permissions
    * Authenticated users only
    
    ### Fields
    Reading this endpoint returns a user object containing the authenticated
    user's public and private data.
    
    Name               | Description                          | Type
    ------------------ | ------------------------------------ | ---------- 
    `url`              | URL of user object                   | _string_
    `id`               | ID of user                           | _integer_
    `phone_number`     | phone number of user object          | _string_
    `full_name`        | full name of user object             | _string_
    `avatar_thumbnail` | URL of user's thumbnail-sized avatar | _string_
    `updated_at`       | last modified date of user object    | _date/time_
    `videos_url` | URL of user's videos sub-collection. **_private_**. |_string_
 
    
    ## Publishing
    You can't create using this endpoint
    
    
    ## Deleting
    You can't delete using this endpoint
    
    
    ## Updating
    Submitting an avatar requires capturing a photo via file upload as 
    **multipart/form-data** then using the `avatar` parameter. 
    
    Note that the request method must still be a PUT/PATCH
    
    ### Permissions
    * Only authenticated users can write to this endpoint.
    
    ### Fields
    Parameter    | Description                    | Type
    ------------ | ------------------------------ | ----------
    `full_name`  | new first name for the  user   | _string_
    `avatar`     | new avatar image for the user. This will be scaled to generate `avatar_thumbnail` | _string_
    
    ### Response
    If update is successful, a user object containing public and private data, 
    otherwise an error message.
        
    
    ## Endpoints
    Name                 | Description                       
    -------------------- | -----------------------------------------------
    [`videos/`](videos/)  | All the videos authenticated user is associated with
    [`activities/`](activities/) | Activities of user's associated videos
    [`recentcontacts/`](recentcontacts/) | Recent contacts of user

    ##
    """
    
    parser_classes = (parsers.JSONParser, parsers.MultiPartParser,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserPrivateSerializer
    queryset = User.objects.all()
            
    def get_object(self):
        """
        Simply return authenticated user.
        No need to check object level permissions
        """
        return self.request.user


class AuthenticatedUserVideoList(generics.ListAPIView):
    """
    List all videos authenticated user is associated with.
    
    ## Reading
    ### Permissions
    * Only authenticated users can read this endpoint.
    
    ### Fields
    Reading this endpoint returns a list of 
    [Video objects](../../videos/hash-key/).
            
    
    ## Publishing
    You can't create using this endpoint
    
    
    ## Deleting
    You can't delete using this endpoint
    
    
    ## Updating
    You can't update using this endpoint
   
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = VideoSerializer

    def get_queryset(self):
        """
        This view should return a list of all videos for the request's user
        """
        user = self.request.user
        
        prefetch_videousers = Prefetch(
            'videousers_set', 
            queryset=VideoUsers.objects.filter(user_id=user.id),
            to_attr='prefetched_videousers')
        
        prefetch_clips = Prefetch(
            'clips', 
            queryset=Clip.objects.select_related('owner'),
            to_attr='prefetched_clips')
        
        prefetch_activity_object_likes = Prefetch(
            'activity_objects',
            queryset=Activity.objects.filter(actor_id=user.id, verb='like'),
            to_attr='prefetched_activity_object_likes'
            )
        
        return Video.objects.filter(
            Q(users__id__in=[user.id]) | Q(owner_id=user.id)).select_related(
            'owner').prefetch_related(
                prefetch_videousers, prefetch_clips, 
                prefetch_activity_object_likes).distinct()
    

class AuthenticatedUserActivityList(generics.ListAPIView):
    """
    List all activities of videos the authenticated user is associated with.
    
    ## Reading
    ### Permissions
    * Only authenticated users can read this endpoint.
    
    ### Fields
    Reading this endpoint returns a list of Activity objects.
        
    Name         | Description                        | Type
    ------------ | ---------------------------------- | ------------------------
    `id`         | Unique identifier                  | _integer_
    `actor`      | Activity's actor                   | _User object_
    `verb`       | Activity's verb                    | _string_
    `object`     | Activity's object                  | _User/Clip/Video object_
    `target`     | Activity's target                  | _User/Clip/Video object_
    `created_at` | Activity's creation date/time      | _date/time_
    
    
    ## Publishing
    You can't create using this endpoint
    
    
    ## Deleting
    You can't delete using this endpoint
    
    
    ## Updating
    You can't update using this endpoint
   
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ActivitySerializer
    pagination_class = ActivityCursorPagination

    def get_queryset(self):
        """
        This view should return a list of all videos for the request's user
        """
        # get user's associated videos
        user = self.request.user
        videos = Video.objects.filter(
            Q(users__id__in=[user.id]) | Q(owner_id=user.id))
        
        return Activity.objects.filter(
            Q(target_videos__in=videos) | Q(object_videos__in=videos)
            ).select_related('actor').prefetch_related(
            'object', 'target').order_by('-created_at')
            

class AuthenticatedUserRecentContactList(generics.GenericAPIView):
    """
    List all recent contacts of authenticated user
    
    ## Reading
    ### Permissions
    * Only authenticated users can read this endpoint.
    
    ### Fields
    Reading this endpoint returns a list of 
    [User objects](../../users/+18005551234/).
            
    
    ## Publishing
    You can't create using this endpoint
    
    
    ## Deleting
    You can't delete using this endpoint
    
    
    ## Updating
    You can't update using this endpoint
   
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserPublicSerializer
        
    def get(self, request, *args, **kwargs):
        """
        This view should return a list of all recent contacts of the
        request's user
        """
        user = request.user
        contacts_ids = Activity.objects.filter(
            actor_id=user.id, 
            verb='invite').prefetch_related('object').order_by(
            '-created_at').values_list('object_id', flat=True).distinct()
        
        contacts_ids = list(contacts_ids)
        contacts = list(User.objects.filter(id__in=contacts_ids).exclude(
                id=user.id))
        contacts.sort(key=lambda c: contacts_ids.index(c.id))
        
        recent_contacts = contacts[:settings.ACCOUNT_MAX_RECENT_CONTACTS]
        serializer = self.get_serializer(recent_contacts, many=True)
        return Response({'results': serializer.data})
    
        
# ------------------------------------------------------------------------------
# USER ACCOUNT AND CREDENTIALS MANAGEMENT
# ------------------------------------------------------------------------------
@api_view(('GET',))
def account_root(request, format=None):
    """
    List the endpoints used for account and credentials managements.
    """
    return Response({
            'Obtain Authentication Token': reverse(
                'obtain_auth_token', request=request, format=format),
            'Activate Account': reverse('activate_user', request=request, 
                                        format=format),
            })


class ObtainExpiringAuthToken(ObtainAuthToken):
    """
    Subclass of `rest_framework.authtoken.views.ObtainAuthToken` that refreshes 
    and returns the authentication token each time it is requested.
    
    ## Reading
    You can't read using this endpoint.
    
    
    ## Publishing
    ### Permissions
    * Anyone can __POST__ using this endpoint.
    
    ### Fields
    Parameter      | Description                                 | Type
    -------------- | ------------------------------------------- | ---------- 
    `phone_number` | phone number for the user. **Required**     | _string_
    `password`     | password for the user. **Required**         | _string_
    
    ### Response
    If  is successful, the authentication token, otherwise an error message. 
    
    Receiving the HTTP CODE, `HTTP_400_BAD_REQUEST`, means that maybe you
    should try re-activating this user account or creating a new one.
    
    Name           | Description                              | Type
    -------------- | ---------------------------------------- | ---------- 
    `token`        | Authentication Token for request headers | _string_
    
    
    ## Deleting
    You can't delete using this endpoint
    
    
    ## Updating
    You can't update using this endpoint
    
    """
    serializer_class = AuthTokenSerializer
    authentication_classes = () # No need to authenticate, wastes time
    permission_classes = (permissions.AllowAny,)
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
        
    def post(self, request,  *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # get or create user's corresponding token
        token, created = AuthToken.objects.get_or_create(
            user=serializer.validated_data['user'])
            
        # a stale token is one that is older than SESSION_COOKIE_AGE
        stale_token = ((timezone.now() - token.updated_at) > 
                       timedelta(seconds=settings.SESSION_COOKIE_AGE))
            
        if not created and stale_token:
            # refresh the token if it isn't newly created and it's stale
                            
            # attempt creating a new and unique key. Don't want to keep looping
            # while making DB calls so will give this one-shot. If the
            # first key generated is unique then use it, else tough luck.
            new_key = token.generate_key()
            if AuthToken.objects.filter(key=new_key).count() == 0:
                token.key = new_key
            
            # saving auto-updates the updated_at field.
            token.save()
            
        # finally return token to user
        return Response({'token': token.key})


class ActivateAccount(APIView):
    """
    Activates a given user's account and also sets the user's password.
    
    ## Reading
    You can't read using this endpoint.
    
    
    ## Publishing
    ### Permissions
    * Anyone can __POST__ using this endpoint.
    
    ### Fields
    Parameter           | Description                                | Type
    ------------------- | ------------------------------------------- | --------
    `phone_number`      | phone number for the new user. **Required** | _string_
    `password`          | password for the new user. **Required**     | _string_
    `verification_code` | verification code expected for activation. **Required** | _integer_
    
    ### Response
    If successful, **_true_**, else an error message.
        
    
    ## Deleting
    You can't delete using this endpoint
    
    
    ## Updating
    You can't update using this endpoint
    
    """
    throttle_classes = ()
    permission_classes = ()
    serializer_class = ActivateAccountSerializer
    
    def post(self, request,  *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        verification_code = serializer.validated_data['verification_code']
        password = serializer.validated_data['password']
        activated = RegistrationProfile.objects.activate_user(
            user, verification_code, password)
        
        if activated:
            return Response({'detail': True})
        else:
            return Response({'detail': "Could not activate user."}, 
                            status=status.HTTP_400_BAD_REQUEST)
