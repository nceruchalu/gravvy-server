from django.contrib import admin
from gravvy.apps.activity.models import Activity

# Register your models here.

class ActivityAdmin(admin.ModelAdmin):
    """
    ModelAdmin associated with the Activity model.
    """
    date_hierarchy = 'created_at'
    list_display = ('__unicode__', 'actor', 'verb', 'object', 'target',)
    list_filter = ('verb',)
    search_fields = ('actor__phone_number', 'actor__full_name')
    
    def get_queryset(self, request):
        """
        Prefetch generic relationships
        """
        qs = super(ActivityAdmin, self).get_queryset(request)
        return qs.select_related('actor').prefetch_related('object', 'target')

admin.site.register(Activity, ActivityAdmin)
