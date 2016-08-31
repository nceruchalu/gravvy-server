"""
Corresponding PhoneNumber field for rest_framework's serializers
"""
from django.core import validators
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from rest_framework.fields import Field, empty
from rest_framework import serializers

# imports from containing package: phonenumber_field
from phonenumber import PhoneNumber
from validators import validate_international_phonenumber

class PhoneNumberField(Field):
    """
    A field to handle PhoneNumber model attributes
    """
    
    type_name = 'PhoneNumberField'
    
    default_error_messages = {
        'blank': _('This field may not be blank.'),
        'invalid': _("Enter a valid E.164 format phone number."),
    }
    default_validators = [validate_international_phonenumber]

    
    def __init__(self, *args, **kwargs):
        self.max_length = 16 # 15 digits and '+' sign
        self.allow_blank = kwargs.pop('allow_blank', False)
        super(PhoneNumberField, self).__init__(*args, **kwargs)
        self.validators.append(validators.MaxLengthValidator(self.max_length))
        
    def run_validation(self, data=empty):
        # Test for the empty string here so that it does not get validated,
        # and so that subclasses do not need to handle it explicitly
        # inside the `to_internal_value()` method.
        if data == '':
            if not self.allow_blank:
                self.fail('blank')
            return ''
        return super(PhoneNumberField, self).run_validation(data)
        
    def to_representation(self, obj):
        """
        Convert a PhoneNumber instance into a primitive, serializable datatype.
        
        Args:
            obj: an instance of PhoneNumber
    
        Returns:
            A string type
        """
        if obj is None:
            return obj
        
        obj = PhoneNumber.to_python(obj)
        if isinstance(obj, six.string_types):
            # it is an invalid phone number
            return obj
        return obj.as_e164
    
    
    def to_internal_value(self, value):
        """
        Restore a primitive datatype into its PhoneNumber representation.
        
        Args:
            value: The number that we are attempting to parse. This can be:
                * an instance of PhoneNumber
                * a string representing phone number
                * invalid data
    
        Returns:
            A PhoneNumber class instance
        """
        phone_number = PhoneNumber.to_python(value)
        
        if phone_number and not phone_number.is_valid():
            raise serializers.ValidationError(self.error_messages['invalid'])
            
        return phone_number
