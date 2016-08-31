import binascii
import os
import random
import datetime

from django.db import models, transaction
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin)
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.conf import settings

from imagekit.models import ImageSpecField
from imagekit.processors import SmartResize, Adjust, Transpose

from gravvy.utils import get_upload_path
from gravvy.apps.push.utils import send_sms_message
from gravvy.fields.phonenumber_field.modelfields import PhoneNumberField

# Create your models here.

#-------------------------------------------------------------------------------
# Custom User Model
#-------------------------------------------------------------------------------

# HELPER FUNCTIONS
def get_avatar_path(instance, filename):
    return get_upload_path(instance, filename, 'img/u/')


class UserManager(BaseUserManager):
    """
    Custom UserManager for the custom AbstractUser
    """
    
    def _create_user(self, phone_number, password,
                     is_staff, is_superuser, is_active=True, **extra_fields):
        """
        Creates and saves a User with the given phone number and password.
        
        Args:
            phone_number: user phone number
            password: user password
            is_staff: whether user can log in to admin UI or not.
            is_superuser: whether user is staff with all permissions or not
            is_active: whether user is able to authenticate on service or not.
            **extra_fields: extra user model fields
            
        Returns:
            account.models.User object
         
        Raises:
            ValueError: phone number is not set
        """
        now = timezone.now()
        if not phone_number:
            raise ValueError('The given phone number must be set')
        user = self.model(phone_number=phone_number,
                          is_staff=is_staff, is_active=is_active,
                          is_superuser=is_superuser,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        """
        Creates and saves a User with the given phone number and password.
        
        Args:
            phone_number: user phone number
            password: user password
            **extra_fields: extra user model fields
            
        Returns:
            account.models.User: regular user
         
        Raises:
            ValueError: phone number is not set
        """
        return self._create_user(phone_number, password, 
                                 False, False, **extra_fields)

    def create_superuser(self, phone_number, password, **extra_fields):
        """
        Creates and saves a User with the given phone number and password.
        
        Args:
            phone_number: user phone number
            password: user password
            **extra_fields: extra user model fields
            
        Returns:
            account.models.User: admin user
         
        Raises:
            ValueError: phone number is not set
        """
        return self._create_user(phone_number, password, 
                                 True, True, **extra_fields)
    
    def get_user_by_number(self, phone_number):
        """
        Get a user that already exists in our system or create a new, inactive 
        `User` with a random password. This user has the provided phone number.
        This is the reason we have an `is_active` flag on the User object- so
        that we can access users on our system before they've signed up.
                                
        Args:
            phone_number: user's phone number
                            
        Returns:
            User instance
        
        Raises:
            ValidationError: Invalid input for a PhoneNumber instance
        """
        try:
            user = self.model.objects.get(phone_number=phone_number)
        except self.model.DoesNotExist:
            user = self._create_user(phone_number, get_random_string(), 
                                     False, False, is_active=False)
        return user


class AbstractUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with admin-compliant permissions.
    Django's default user doesn't work for us as we dont support username
    but instead phone number as the unique identifier field.
    
    Phone number and password are required. Other fields are optional.
    
    There is an interesting note about the context of "is_active" in this model.
        When an app user invites a number of address book contacts, not all
        those contacts will be registered on the service. These unregistered
        contacts will be represented as inactive users (is_active = False). If
        these contacts eventually sign up to the service all their posts and
        messages will simply be waiting for them.
    
    The following fields are inherited from the superclasses:
        * password
        * last_login
        * is_superuser
    """
    
    phone_number = PhoneNumberField(
        _('phone number'), unique=True, 
        help_text=_("Required. E.164 format phone number."), 
        error_messages={
            'unique': _("A user with that phone number already exists."),
            })
    full_name = models.CharField(_('full name'), max_length=30, blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False,help_text=_(
            'Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(_('active'), default=True, help_text=_(
            'Designates whether this user should be treated as '
            'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = True

    def get_full_name(self):
        """
        Returns the name.
        """
        full_name = '%s (%s)' % (self.full_name, self.phone_number)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.full_name or self.phone_number.as_e164
    

class User(AbstractUser):
    """
    Concrete User class. It's an extension of AbstractUser class.
    """
    
    # last modified date to be used by client apps for sync purposes.
    # ref: http://stackoverflow.com/a/5052208
    updated_at = models.DateTimeField(_('last update date/time'), auto_now=True)
    
    # avatar
    avatar = models.ImageField(
        _('profile picture'), upload_to=get_avatar_path, blank=True)
    
    # imagekit spec for avatar shown in mobile app's UITableViews
    # The Transpose processor will use the metadata in the image and rotate by 
    # the specified amount. This ensures the image will be the right orientation
    # We put this processor first as subsequent processors will strip the
    # metadata from the image.
    avatar_thumbnail = ImageSpecField(
        source='avatar',
        processors=[Transpose(Transpose.AUTO),
                    SmartResize(width=settings.AVATAR_THUMBNAIL_SIZE, 
                                height=settings.AVATAR_THUMBNAIL_SIZE),
                    Adjust(contrast = 1.2, sharpness=1.1)],
        format='JPEG',
        options={'quality':90})
    
    # this is used for tracking avatar changes
    # ref: http://stackoverflow.com/a/1793323
    __original_avatar = None
    
    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'
        
    def get_avatar_thumbnail_url(self):
        """
        get url of avatar's thumbnail. If there isn't an avatar_thumbnail then
        return an empty string
        """
        return self.avatar_thumbnail.url if self.avatar_thumbnail else ''
    
    def get_absolute_url(self):
        return reverse('user-detail', kwargs={'phone_number':self.phone_number})
        
    def get_full_name(self):
        """
        Get user's full name
        If there is a valid full name then use that, otherwise use the 
        phonenumber [prepended with a 'tel:']
    
        Args:   
            None

        Returns:      
            (str) user's full name
        """
        return (super(User, self).get_full_name() or ('tel:'+self.phone_number))
    
    def __unicode__(self):
        """
        Override the representation of users to use full names.
        
        Args:   
            None
            
        Returns:      
            (str) user's full name
        """
        return self.get_full_name()
    
    def delete_avatar_files(self, instance):
        """
        Delete a user's avatar files in storage
            * First delete the user's ImageCacheFiles on storage. The reason 
              this must happen first is that deleting source file deletes the 
              associated ImageCacheFile references but not the actual 
              ImageCacheFiles in storage.
            * Next delete source file (this also performs a delete on the 
              storage backend)
                
        Args:   
            instance: User object instance to have files deleted
        
        Returns:      
            None 
        """
        # get avatar_thumbnail location and delete it
        instance.avatar_thumbnail.storage.delete(instance.avatar_thumbnail.name)
        # delete avatar
        instance.avatar.delete()
    
    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.__original_avatar = self.avatar
    
    def save(self, *args, **kwargs):
        """
        On instance save ensure old image files are deleted if images are 
        updated.
                            
        Args:   
            *args: all positional arguments
            **kwargs: all keyword arguments

        Returns:
            None 
        """
        if self.__original_avatar and self.avatar != self.__original_avatar:
            # avatar has changed and this isn't the first avatar upload, so
            # delete old files.
            orig = User.objects.get(pk=self.pk)
            self.delete_avatar_files(orig)
                    
        super(User, self).save(*args, **kwargs)
        # update the image file tracking properties
        self.__original_avatar = self.avatar
    
    def delete(self, *args, **kwargs):
        """
        Default model delete() doesn't delete files on storage, so force that to
        happen.
        
        Args:
            *args: all positional arguments
            **kwargs: all keyword arguments

        Returns:
            None 
        """
        # Import Activity here to avoid circular imports
        from django.contrib.contenttypes.models import ContentType
        from gravvy.apps.activity.models import Activity
        
        # if there were image files, delete those
        if self.avatar:
            self.delete_avatar_files(self)
            
        # cleanup related Activities
        content_type = ContentType.objects.get_for_model(self)
        Activity.objects.filter(
            models.Q(object_id=self.id, object_content_type=content_type) |
            models.Q(target_id=self.id, target_content_type=content_type)
            ).delete()
                        
        super(User, self).delete(*args, **kwargs)
        

#-------------------------------------------------------------------------------
# Authentication Token Model
#-------------------------------------------------------------------------------

class AuthToken(models.Model):
    """
    Customized authorization token model.
    Having `key` as primary_key like rest-framework did makes it impossible to
    update it. So I'll make it unique instead
    """
    key = models.CharField(max_length=40, unique=True)
    user = models.OneToOneField(User, related_name='auth_token')
    created_at = models.DateTimeField(_('creation date/time'), 
                                      auto_now_add=True)
    updated_at = models.DateTimeField(_('last update date/time'), auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(AuthToken, self).save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __unicode__(self):
        return self.key


#-------------------------------------------------------------------------------
# User Registration Model
#-------------------------------------------------------------------------------
class RegistrationManager(models.Manager):
    """
    Custom Model Manager for the RegistrationProfile class.
    
    We use this as it is the preferred way to add "table-level" functionality
    to the model.
    The methods defined here provide shortcuts for account creation and 
    (re)activation (including generation and SMS sending of verification code)
    """
    
    def activate_user(self, user, verification_code, password):
        """
        Validate a verification code and activate the corresponding `User` 
        instance if valid. After successful activation set the user's password 
        to the new value.
        
        Args:
            user: user who submitted a particular verification code
            verification_code: Verification code to check against.
            password: if user is activated, this will be the new password
        
        Returns:
            Successful/Failed activation
        """
        success = False
        
        try:
            # first check that code is valid
            registration_profile = self.get(user=user)
            if (registration_profile.verification_code == verification_code) \
                    and not registration_profile.verification_code_expired():
                user.is_active = True
                user.set_password(password)
                user.save()
                success = True
                            
        except self.model.DoesNotExist:
            pass # nothing to do
              
        return success
    
    
    @transaction.atomic
    def get_or_create_inactive_user(self, phone_number, password, 
                                    send_sms=True):
        """
        Get a user that already exists in our system or create a new, inactive 
        `User`. 
        
        Generate a `RegistrationPofile and possibly SMS its verification code 
        to the `User`.
        
        Args:
            phone_number: user's phone number
            password: user's password
            send_sms: flag indicator of if an SMS should be sent to the new
                user. It defaults to True so disable by setting to False.
                
        Returns:
            Inactive `User` instance
        """
        try:
            user = User.objects.get(phone_number=phone_number)
            
        except User.DoesNotExist:
            user = User.objects._create_user(phone_number, password,
                                             False, False, is_active=False)
        
        registration_profile = self.create_or_update_profile(user)
        
        if send_sms:
            registration_profile.send_verification_sms()
        
        return user

    
    def create_or_update_profile(self, user):
        """
        Create/Update a RegistrationProfile for a given User. We potentially
        update a user if there's a need to reverify the phone number of an
        existing user
        
        Args:
            user: User to associate with a new or updated RegistrationProfile.
            
        Returns:
            RegistrationProfile instance
        """
        num_digits = settings.ACCOUNT_VERIFICATION_CODE_LEN
        min_code = 10**(num_digits-1)
        max_code = 10**(num_digits) - 1
        verification_code = random.randint(min_code, max_code)
        
        try:
            registration_profile = self.select_related('user').get(user=user)
            registration_profile.verification_code = verification_code
            registration_profile.save()
            
        except self.model.DoesNotExist:
            registration_profile = self.create(
                user=user, verification_code=verification_code)
        
        return registration_profile
        

class RegistrationProfile(models.Model):
    """
    A simple profile which stores a verification code for use during user
    account registration/verification.
    
    Generally, you will not want to interact directly with instances of this
    model; the provided manager includes methods for creating and (re)activating
    users.
  
    """
    user = models.OneToOneField(User, related_name='registration_profile')
    verification_code = models.PositiveIntegerField(_('verification code'))
    
    created_at = models.DateTimeField(
        _('date created'), default=timezone.now, 
        help_text=_('creation date/time'))
    
    # The date/time of setting the verification_code. Note that this isn't a
    # "date added" field as the verification code will need to be reset each
    # time the user reformats the phone and re-installs the app.
    # This date will be used for checking if verification codes have expired.
    updated_at =  models.DateTimeField(
        _('last update date/time'), auto_now=True)
    
    objects = RegistrationManager()
    
    class Meta:
        verbose_name = _('registration profile')
        verbose_name_plural = _('registration profiles')
    
    def __unicode__(self):
        return u"Registration information for %s" % self.user
    
    def verification_code_expired(self):
        """
        Determine whteher this RegistrationProfile's activation key
        has expired.
        
        Code expiration is determined by a two-step process:
            1. The date the registration_profile was updated is incremented by
               the number of days specified in settings.ACCOUNT_ACTIVATION_DAYS.
            2. If the is less than or equal to the current date, the code
               has expired and this methods returns true.
        
        Returns:
            Boolean indicator: True if key has expired, otherwise False.
        """
        expired = False
        expiration_delta = datetime.timedelta(
            days=settings.ACCOUNT_ACTIVATION_DAYS)
        return ((self.updated_at + expiration_delta) <= timezone.now())

    def send_verification_sms(self):
        """
        Send verification code to user via SMS to user
        """        
        message = "Your Gravvy code is %s. Use this to verify your device." \
            % (str(self.verification_code))
        send_sms_message(self.user, message)
        
    
