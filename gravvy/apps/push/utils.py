"""
Utility functions that come in handy for push notifications

Table Of Contents:
    send_sms_message: send an SMS to a given phone number
    send_bulk_sms_message: Send bulk SMS message to multiple users
    send_push_message: Send a PUSH notification to a given user
    send_bulk_push_message: Send a bulk PUSH notification to multiple users
"""

import plivo
from django.conf import settings
from django.db.models import Q
from push_notifications.models import APNSDevice

def send_sms(phone_number, message):
    """
    Send an SMS message to a given phone number
    
    Args:
        phone_number: E.164 format phone number to send message to without the
            leading + sign
        message: SMS text body
        
    Returns:
        None
    """
    if (phone_number is not None) and (message is not None):
        # phone number shouldn't have a + sign per plivo docs
        phone_number = ''.join(c for c in phone_number if c.isalnum())
        
        plivoAPI = plivo.RestAPI(settings.PLIVO_AUTH_ID, 
                                 settings.PLIVO_AUTH_TOKEN)
        params = {'src' : settings.PLIVO_NUMBER, 
                  'dst' : phone_number, 
                  'text' : message, 
                  'type' : 'sms'}
        if settings.PLIVO_DEBUG:
            # Dont bother wasting credits when just testing out
            print params
        else:
            plivoAPI.send_message(params)


def send_sms_message(user, message):
    """
    Send an SMS message to a given user
    
    Args:
        user: user to send message to
        message: SMS text body
        
    Returns:
        None
    """
    send_sms(user.phone_number.as_e164, message)


def send_bulk_sms_message(users, message):
    """
    Send bulk SMS messages to multiple users
    
    Args:
        user: users to send message to
        message: SMS text body
        
    Returns:
        None
    """
    for user in users:
        send_sms(user.phone_number.as_e164, message)


def get_user_badge(user):
    """
    Get badge for a given user
    
    Args:
        user: user to get badge for
        
    Returns:
        badge_count of None if count is 0
    """
    from gravvy.apps.video.models import VideoUsers
    
    device_badge = VideoUsers.objects.filter(
        Q(user_id=user.id),
        Q(status=VideoUsers.STATUS_INVITED) | 
        Q(new_likes_count__gt=0) | Q(new_clips_count__gt=0)
        ).distinct().count()
    if device_badge == 0:
        device_badge = None
    return device_badge

def send_push_message(user, message, badge=None, extra={}):
    """
    Send a PUSH notification to a given user
    
    Args:
        user: user to receive the push notification
        message: message to be shown when app is in background/inactive
        badge: badge to be shown on the ap
        extra: extra content to be consumed by the app when active
        
    Returns:
        None
    """
    device_badge = get_user_badge(user)
    send_bulk_push_message([user], message, device_badge, extra)


def send_bulk_push_message(users, message, badge=None, extra={}):
    """
    Send a bulk PUSH notification to multiple users
    
    Args:
        users: users to receive the push notification
        message: message to be shown when app is in background/inactive
        extra: extra content to be consumed by the app when active

    Returns:
        None
    """
    # only send sound if there there's a message
    sound = settings.PUSH_SOUND_FILE if message else None
    
    # get all devices associated with given users
    devices = APNSDevice.objects.filter(user__in=users).select_related('user')
    for device in devices:
        # can't invoke bulk messaging functionality as each user has a
        # unique badge count
        device_badge = get_user_badge(device.user)
        device.send_message(message, sound=sound, badge=device_badge, 
                            extra=extra)

