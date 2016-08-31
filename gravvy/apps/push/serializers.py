"""
Provides a way of serializing and deserializing the push_notifications app model
instances into representations such as json.
"""
from django.utils import timezone

from rest_framework import serializers
from push_notifications.models import Device, APNSDevice, GCMDevice

from gravvy.apps.account.serializers import UserPublicSerializer

import re

# Match UUID that are exactly 64 hexacdecimal characters. The `\Z` matches the
# end of the string (vs. `$` which would match the end of a string or a newline)
HEX64_RE = re.compile("[0-9a-f]{64}\Z", re.IGNORECASE)

class AbstractBaseDeviceSerializer(serializers.ModelSerializer):
    """
    Abstract base serializer to be used for registering devices.
    The APNS and GCM device serializers are to build off of this.
    """
    
    user = UserPublicSerializer(read_only=True)
    
    class Meta:
        model = Device
        abstract = True
        fields = ('user', 'name', 'registration_id', 'active', 'date_created',)
        read_only_fields = ('active', 'date_created',)
    
    def create(self, validated_data):
        """
        Instantiate a new Device instance or get one that already exists 
        and update the user 
        """
        
        registration_id = validated_data.get('registration_id')
        user = self.context['request'].user
        ModelClass = self.Meta.model
        
        try:
            device = ModelClass.objects.get(registration_id=registration_id)
            device.user = user
            device.date_created = timezone.now()
            device.save()
                        
        except ModelClass.DoesNotExist:
            device = ModelClass.objects.create(registration_id=registration_id, 
                                               user=user)
        
        # Delete any other device tied to this user
        # This ensures each user only has one device identified by phone number
        ModelClass.objects.filter(user=user).exclude(id=device.id).delete()
            
        return device


class APNSDeviceSerializer(AbstractBaseDeviceSerializer):
    """
    Serializer to be used for registering iOS device APNS tokens
    """
    
    # registration_id can't be expected to be unique here so redefine it
    # to remove the UniqueValidator
    registration_id = serializers.CharField(
        label='Registration ID', max_length=64)
        
    class Meta:
        model = APNSDevice
        fields = ('user', 'name', 'registration_id', 'active', 'date_created',)
        read_only_fields = ('active', 'date_created',)
         
    def validate_registration_id(self, value):
        """
        Ensure iOS device tokens are 256-bit hexadecimal (64 characters)
        """
        registration_id = value
        if not value or HEX64_RE.match(value) is None:
             raise serializers.ValidationError(
                "Registration ID (device token) is invalid.")
        return value


class GCMDeviceSerializer(AbstractBaseDeviceSerializer):
    """
    Serializer to be used for registering Android Device GCM tokens
    
    Note:
        - Unlike, APNS there isn't any documented validation we can perform
          on the GCM registration_id other than ensuring it be present
    """
    
    class Meta:
        model = GCMDevice
        fields = ('user', 'name', 'registration_id', 'active', 'date_created',)
        read_only_fields = ('active', 'date_created',)

        
    def create(self, validated_data):
        """
        Unfortunatley the registration_id of GCMDevices isn't unique so prune
        duplicates
        """
        registration_id = validated_data.get('registration_id')
        devices = GCMDevice.objects.filter(registration_id=registration_id)
        if (devices.count() > 1):
            devices.delete()
        
        return super(GCMDeviceSerializer, self).create(validated_data)
    
