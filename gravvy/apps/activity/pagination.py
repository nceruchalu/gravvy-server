"""
Custom Pagination subclasses to be used by the activity app
"""
from rest_framework import pagination

class ActivityCursorPagination(pagination.CursorPagination):
    """
    A cursor-based pagination scheme that orders objects by the `created_at` 
    field in DESC order.
        
    http://www.django-rest-framework.org/api-guide/pagination/#cursorpagination
    """
    ordering = '-created_at'
    page_size = 100
    
