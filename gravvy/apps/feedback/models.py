from django.db import models
from django.utils import timezone

from gravvy.apps.account.models import User

# Create your models here.

class Feedback(models.Model):
    """
    In-App User Feedback
    """
    body = models.TextField()
    user = models.ForeignKey(User, related_name="feedbacks")
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    
    class Meta:
        ordering = ['-created_at']
        
    def __unicode__(self):
        return self.body
