"""
Permissions for REST API
"""

from rest_framework import permissions
from gravvy.apps.account.models import User

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of a user object to edit it.
    All other users can read the user object.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow
        # GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the request's associated
        # user object.
        return obj == request.user


class IsDetailOwner(permissions.BasePermission):
    """
    Global permission check to  only allow access to the owner of the data in a
    detail view (or a view with a lookup_field).
    
    Expects to be used on a detail view or a view with a lookup_field
    """
    
    def has_permission(self, request, view):
        user_owns_detail_view = False
                
        lookup_url_kwarg = view.lookup_url_kwarg or view.lookup_field
        lookup = view.kwargs.get(lookup_url_kwarg, None)
            
        if lookup is not None:
            user_owns_detail_view = request.user.phone_number.as_e164 == lookup
            
        # permissions are only allowed to owner of the detail.
        return user_owns_detail_view
