"""
activity app model

Refs:
    Atom Activity Streams 1.0 spec:
      - http://activitystrea.ms/specs/atom/1.0/
    Model based off:
      - https://github.com/justquick/django-activity-stream [great but bloated]
      - https://github.com/paulosman/django-activity
"""
from collections import OrderedDict

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timesince import timesince as djtimesince
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from gravvy.apps.account.models import User
from gravvy.apps.activity.signals import activity
from gravvy.apps.activity.utils import activity_handler
from gravvy.apps.activity import schema


# Create your models here.
class Activity(models.Model):
    """
    Activity describes an actor acting out a verb (on an optional object) 
    (to an optional target)
    Nomenclature based on http://activitystrea.ms/specs/atom/1.0/
        `actor`:  the object that performed the activity
        `verb`:   the verb phrase that identifies the action of the activity
        `object`: the object linked to the action itself
        `target`: the object to which the activity was performed
    
    Generalized Format:
        <actor <verb> <time>
        <actor <verb> <target> <time>
        <actor <verb> <object> <target> <time>
    
    Examples:
        <noddy> <created a video> <1 minute ago>
        <nkemka> <followed> <drkems> <2 days ago>
        <drkems> <added> <clip:3> to <video:demo> <2 hours ago>
        
    Unicode Representation (`Title` in spec):
        nceruchalu created a video 1 minute ago
        nkemka followed drkems 2 days ago
        drkems added clip to video:demo 2 hours ago
        
    HTML Representation (`Summary` in spec):
        <a href="/u/9/">drkems</a> added <a href="/c/11/">clip</a> to 
          <a href="/v/11/">demo</a> 2 hours ago    
    """
    # actor
    actor = models.ForeignKey(User, related_name="activities", 
                              verbose_name=_('actor'))
    
    # verb
    verb = models.CharField(
        _('verb'), max_length=50, choices=schema.VERB_CHOICES)
    
    # object
    object_content_type = models.ForeignKey(
        ContentType, related_name='object', 
        blank=True, null=True, db_index=True)
    object_id = models.PositiveIntegerField(
        blank=True, null=True, db_index=True)
    object = GenericForeignKey('object_content_type', 'object_id')
    
    # target
    target_content_type = models.ForeignKey(
        ContentType, related_name='target', 
        blank=True, null=True, db_index=True)
    target_id = models.PositiveIntegerField(
        blank=True, null=True, db_index=True)
    target = GenericForeignKey('target_content_type', 'target_id')
    
    # time
    created_at = models.DateTimeField(
        _('activity timestamp/date created'), default=timezone.now, 
        db_index=True)
    
    class Meta:
        ordering=('-created_at',)
    
    def __unicode__(self):
        ctx = {
            'actor': self.actor,
            'verb': OrderedDict(schema.VERBS)[self.verb][0],
            'object': self.object,
            'target': self.target,
            'timesince': self.timesince()
        }
        if self.target:
            # if there is a <target>, then there might also be an <object>
            if self.object:
                # if there is a <target> and an <object>
                return u'%(actor)s %(verb)s %(object)s to %(target)s %(timesince)s ago' % ctx
            # if there is a <target> and no <object>
            return u'%(actor)s %(verb)s %(target)s %(timesince)s ago' % ctx
        
        if self.object:
            # if there isn't a <target> but there is an <object>
            return u'%(actor)s %(verb)s %(object)s %(timesince)s ago' % ctx
        
        # if there isn't a <target> and there isn't an <object>
        return u'%(actor)s %(verb)s %(timesince)s ago' % ctx
    
    def timesince(self, now=None):
        """
        Get time since this activity instance was created.
        Effectively a shortcut for django.utils.timesince.timesince
                   
        Args:   
            now: datetime.datetime instance to start time comparison
        Returns:    
            (str) nicely formatted time e.g. "10 minutes"
        """
        return djtimesince(self.created_at, now)
    
    def actor_url(self):
        """
        Get the URL to the user view for the actor.
                   
        Args:   
            None
        Returns:
            URL of `actor` object
        """
        return self.actor.get_absolute_url() if self.actor else None
        
    def target_url(self):
        """
        Get the URL to the view for the target.
                   
        Args:
            None
        Returns:
            URL of `target` object
        """
        return self.target.get_absolute_url() if self.target else None
        
    def object_url(self):
        """
        Get the URL to the view for the object.
                   
        Args:
            None
        Returns:
            URL of `object` object
        """
        return self.object.get_absolute_url() if self.object else None


# connect the signal
activity.connect(activity_handler, dispatch_uid="gravvy.apps.activity.models")
