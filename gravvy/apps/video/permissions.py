"""
Permissions for REST API
"""

from rest_framework import permissions
from gravvy.apps.video.models import Video, VideoUsers
from gravvy.apps.account.models import User

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of a video/clip object to edit 
    it. All other users can read the video object.
    
    Assumptions:
        video/clip object has an `owner` property that is a foreign key to User
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the object's associated owner
        return obj.owner_id == request.user.id


class IsAssociatedUser(permissions.BasePermission):
    """
    Global-level permission to only allow the owner and associated users of
    video objects to make edits on its sub-views, such as inviting new users.
    All other users simply have no access.

    Assumptions:
        - expects to be used on a detail view or a view with a lookup_field
    """
    
    def has_permission(self, request, view):
        user_is_associated = False
                
        try:
            lookup_url_kwarg = view.lookup_url_kwarg or view.lookup_field
            lookup = view.kwargs.get(lookup_url_kwarg, None)
            
            if lookup is not None:
                videousers_lookup_field = 'video__' + view.lookup_field
                filter_kwargs = {videousers_lookup_field: lookup,
                                 'user_id': request.user.id}
                user_is_associated = VideoUsers.objects.filter(
                    **filter_kwargs).exists()
                
                if not user_is_associated:
                    # no VideoUsers object, so check if user is owner and
                    # oddly without an associated VideoUsers object
                    filter_kwargs = {view.lookup_field: lookup}
                    video = Video.objects.get(**filter_kwargs)
                    user_is_associated = video.owner_id == request.user.id

        except Video.DoesNotExist:
            pass
        
        # Write permissions are only allowed to the object's associated user
        return user_is_associated


class IsAssociatedUserOrReadOnly(IsAssociatedUser):
    """
    Global-level permission to only allow the owner and associated users of
    video objects to make edits on its sub-views, such as uploading clips.
    All other users can simply read.

    Assumptions:
        - expects to be used on a detail view or a view with a lookup_field
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Other request methods require being an associated user
        return super(IsAssociatedUserOrReadOnly, self).has_permission(
            request, view)
  

class IsUserDetailOwner(permissions.BasePermission):
    """
    Global permission to only allow writes by owner of the user data in a
    detail view. All other users can read the object.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
                
        phone_number_lookup = view.kwargs.get('phone_number', None)
        
        user_owns_detail_view = False
        if phone_number_lookup is not None:
            user_owns_detail_view = (
                request.user.phone_number.as_e164 == phone_number_lookup) 
        
        # permissions are only allowed to owner of the detail.
        return user_owns_detail_view


class IsOwnerOrUserDetailOwner(IsUserDetailOwner):
    """
    Global permission to only allow writes by detail view owner or the owner of 
    the user data. All other users can read the object
    
    Expects to be used on a detail view or a view with a lookup_field
    """
    def has_permission(self, request, view):
        user_is_owner = False
        
        try:
            lookup_url_kwarg = view.lookup_url_kwarg or view.lookup_field
            lookup = view.kwargs.get(lookup_url_kwarg, None)
            
            if lookup is not None:
                filter_kwargs = {view.lookup_field: lookup}
                video = Video.objects.get(**filter_kwargs)
                user_is_owner = (request.user.id == video.owner_id)
                
        except Video.DoesNotExist:
            pass # user_is_owner already set
        
        if user_is_owner:
            # video owner has all permissions
            return True
        else:
            # revert to superclass if user isn't owner.
            return super(IsOwnerOrUserDetailOwner, self).has_permission(
                request, view)


class IsVideoOwnerOrClipOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owner of a video or a clip to edit 
    clip. All other users can read the video object.
    
    Assumptions:
        clip object has an `owner` property that is a foreign key to User
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the object's associated owner
        user_id = request.user.id
        return obj.video.owner_id == user_id or obj.owner_id == user_id
