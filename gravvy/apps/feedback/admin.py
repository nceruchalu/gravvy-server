from django.contrib import admin

from gravvy.apps.feedback.models import Feedback
from gravvy.apps.feedback.forms import FeedbackForm

# Register your models here.

class FeedbackAdmin(admin.ModelAdmin):
    """
    Representation of Feedback model in admin interface with a custom form
    """
    fields = ('user', 'body', 'created_at',)
    list_display = ('created_at', 'body', )
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    form = FeedbackForm
    
admin.site.register(Feedback, FeedbackAdmin)
