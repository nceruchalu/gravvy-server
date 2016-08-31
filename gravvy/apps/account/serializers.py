"""
Provides a way of serializing and deserializing the account app model
instances into representations such as json.
"""
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from rest_framework import serializers
from rest_framework.reverse import reverse

from gravvy.utils import human_readable_size
from gravvy.fields.phonenumber_field import serializerfields, phonenumber
from gravvy.apps.account.models import User, RegistrationProfile
from gravvy.apps.rest.fields import ImageField

class AbstractBaseUserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Abstract base serializer to be used for getting and updating users.
    All other User serializers are to build off of this.
    
    Most fields are read-only. Only writeable field are: 
    - 'full_name'
    - 'avatar'
    """
    
    # url field should lookup by 'phone_number' not the 'pk'
    url = serializers.HyperlinkedIdentityField(
        view_name='user-detail', lookup_field='phone_number')
    
    avatar_thumbnail = serializers.SerializerMethodField()
    
    # ----------------------
    # Private Fields
    # -----------------------
    avatar =ImageField(label='Profile picture', required=False, write_only=True)
    
    # `videos` is a reverse relationship on the User model, so it will not be 
    # included by default when using the HyperlinkedModelSerializer class, so 
    # we need to add an explicit field for it.
    
    # Show a link to the collection of a user's videos
    videos_url = serializers.HyperlinkedIdentityField(
        view_name='user-video-list', lookup_field='phone_number')
    
    class Meta:
        model = User
        abstract = True
    
    def validate_avatar(self, value):
        """
        Check that the uploaded file size is within allowed limits
        """
        imgfile = value
        if imgfile and imgfile.size > settings.MAX_IMAGE_SIZE:
            raise serializers.ValidationError(
                "Ensure this file's size is at most %s (it is %s)."
                % (human_readable_size(settings.MAX_IMAGE_SIZE), 
                   human_readable_size(imgfile.size)))
        return value
    
    def get_avatar_thumbnail(self, obj):
        """
        Get the  absolute URI of the user's avatar thumbnail
        """
        return obj.get_avatar_thumbnail_url()


class UserPublicSerializer(AbstractBaseUserSerializer):
    """
    Serializer class to show a privacy-respecting version of users, i.e. public
    data only and so doesn't disclose personal information like 'profile'
    
    All fields are read-only
    """
    
    class Meta:
        model = User
        fields = ('url', 'id', 'phone_number', 'full_name', 'avatar_thumbnail',
                  'updated_at')
        read_only_fields = ('id', 'phone_number', 'full_name', 'updated_at')


class UserPrivateSerializer(AbstractBaseUserSerializer):
    """
    Serializer class to shows both public and private data.
    'full_name' and 'avatar' are readwrite fields
    """
    
    class Meta:
        model = User
        fields = ('url', 'id', 'phone_number', 'full_name', 'avatar_thumbnail',
                  'avatar', 'videos_url', 'updated_at')
        read_only_fields = ('id', 'phone_number', 'updated_at')
        extra_kwargs = {'avatar': {'write_only': True}}


class UserCreationSerializer(AbstractBaseUserSerializer):
    """
    Serializer to be used for creating users.
    """
    # phone number is a PhoneNumberField so all validation for valid E.164
    # formatting is performed by the serializer
    phone_number = serializerfields.PhoneNumberField()
    
    class Meta:
        model = User
        fields = ('url', 'id', 'phone_number', 'password')
        read_only_fields = ('id',)
        extra_kwargs = {'password': {'write_only': True}}
        
    def create(self, validated_data):
        """
        Create a new user instance
        """
        # create an inactive user and send verification code
        user = RegistrationProfile.objects.get_or_create_inactive_user(
            phone_number=validated_data['phone_number'], 
            password=validated_data['password'])
                    
        return user


class UserNumberSerializer(AbstractBaseUserSerializer):
    """
    Serializer class to show users public data on read and allows for 
    specification of a user's phone number on writes.
    
    This comes in handy when trying to add users (identified by phone numbers) 
    to videos
    """
    # phone number is a PhoneNumberField so all validation for valid E.164
    # formatting is performed by the serializer. field can't be expected to be
    # unique here
    phone_number = serializerfields.PhoneNumberField(
        help_text=_("Required. E.164 format phone number."), 
        label=_('phone number')
        )
    
    class Meta:
        model = User
        fields = ('id', 'phone_number', 'full_name', 'updated_at')
        read_only_fields = ('id', 'full_name', 'updated_at')
        
    def create(self, validated_data):
        """
        Instantiate the User instance associated with the provided phone_number.
        
        This modifies the phone number field in the validated_data object in the
        event it is simply missing a valid country code. A missing country code
        is assumed to be same as that of requesting user.
        """
        user = self.context['request'].user
        phone_number_str = validated_data['phone_number']
        # can only get a default country code if user is authenticated
        if user.is_authenticated():
            default_region = user.phone_number.region_code
                
            # now try and get a valid phone number using the default
            # region. If able to get one update the data object.
            try:
                phone_number_obj = phonenumber.PhoneNumber.from_string(
                    phone_number=phone_number_str, region=default_region)
                if phone_number_obj.is_valid():
                    validated_data['phone_number'] = phone_number_obj.as_e164
            except phonenumber.NumberParseException:
                pass

        number = validated_data.get('phone_number')
        user = User.objects.get_user_by_number(number)
        return user

    
class UserMinimalSerializer(AbstractBaseUserSerializer):
    """
    Serializer to be used for providing minimal information about a User
    necessary for showing it in the activity stream
    """
    class Meta:
        model = User
        fields = ('phone_number', 'full_name', 'avatar_thumbnail', 'updated_at')
        read_only_fields = ('phone_number', 'full_name', 'updated_at')
        

class AuthTokenSerializer(serializers.Serializer):
    """
    customized AuthTokenSerializer
    """
    phone_number = serializerfields.PhoneNumberField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, data):
        phone_number = data['phone_number']
        password = data['password']
        
        if phone_number and password:
            user = authenticate(phone_number=phone_number, password=password)
            
            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise serializers.ValidationError(msg)
            else:
                msg = _('Unable to login with provided credentials.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Must include "email" and "password"')
            raise serializers.ValidationError(msg)
        
        data['user'] = user
        return data


class ActivateAccountSerializer(serializers.Serializer):
    """
    Serializer for activating an account
    """
    phone_number = serializerfields.PhoneNumberField()
    password = serializers.CharField(style={'input_type': 'password'})
    verification_code = serializers.IntegerField()
    
    def validate(self, data):
        phone_number = data['phone_number']
        password = data['password']
        verification_code = data['verification_code']
        
        if phone_number and password and verification_code:
            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                user = None
                        
            if user:
                try:
                    registration_profile = RegistrationProfile.objects.get(
                        user=user)
                    
                except RegistrationProfile.DoesNotExist:
                    msg = _('Must register before attempting activation.')
                    raise serializers.ValidationError(msg)
                
            else:
                msg = _('Unable to login with provided credentials.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Must include "phone_number", "password", and '
                    '"verification code"')
            raise serializers.ValidationError(msg)
        
        data['user'] = user
        return data
