from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from push_notifications.models import APNSDevice, GCMDevice
from push_notifications.admin import DeviceAdmin

# Register your models here.
class CustomDeviceAdmin(DeviceAdmin):
    list_display = ('user', 'registration_id', 'active', 'date_created')
    fields = ('name', 'active', 'user', 'registration_id', 'date_created')
    readonly_fields = ('date_created',)
    search_fields = ('registration_id', 'user__email')
    actions = ('send_message', 'send_message_sound_badge', 'send_bulk_message', 
               'prune_devices', 'enable', 'disable')
    
    def video_for_device(self, device):
        """
        get any video for the user associated with a device
        
        Returns:
            Video object instance or none
        """
        videos = device.user.videos.all().order_by('-created_at')
        return videos[0] if len(videos) > 0 else None
    
    def send_message(self, request, queryset):
        for device in queryset:
            try:
                video = self.video_for_device(device)
                extra = {} # must be an empty dictionary but not None
                if video:
                    extra[settings.PUSH_VIDEO_HASH_KEY_KEY] = video.hash_key
                if device.user:
                    extra[settings.PUSH_VIDEO_USER_PHONE_NUMBER_KEY] = (
                        device.user.phone_number.as_e164)
                    extra[settings.PUSH_VIDEO_USER_FULL_NAME_KEY] = (
                        device.user.full_name)
                
                extra[settings.PUSH_VIDEO_MESSAGE_KEY ] = (
                    'This is what it looks like when a chicken crosses the ' 
                    'road and clucks at the same time. Ideally this message '
                    'would be somewhat long')
                
                device.send_message("Test single notification", extra=extra)
            except Exception as e:
                pass
    send_message.short_description = _("Send test message")
    
    def send_message_sound_badge(self, request, queryset):
        for device in queryset:
            try:
                video = self.video_for_device(device)
                extra = {} # must be an empty dictionary but not None
                if video:
                    extra[settings.PUSH_VIDEO_HASH_KEY_KEY] = video.hash_key
                if device.user:
                    extra[settings.PUSH_VIDEO_USER_PHONE_NUMBER_KEY] = (
                        device.user.phone_number.as_e164)
                    extra[settings.PUSH_VIDEO_USER_FULL_NAME_KEY] = (
                        device.user.full_name)
                
                extra[settings.PUSH_VIDEO_MESSAGE_KEY ] = 'just a message!!'

                device.send_message(
                    "Test single notification with sound and badge", 
                    sound="default", badge=1, extra=extra)
            except Exception as e:
                pass
    send_message_sound_badge.short_description = (
        "Send test message with sound and badge")


# unregister default ModelAdmins
admin.site.unregister(APNSDevice)
admin.site.unregister(GCMDevice)

# register custom ModelAdmins
admin.site.register(APNSDevice, CustomDeviceAdmin)

