"""
field to be used in a django form
"""
from django.utils.translation import ugettext_lazy as _
from django.forms.fields import CharField
from django.core.exceptions import ValidationError

# imports from containing package: phonenumber_field
from phonenumber import PhoneNumber
from validators import validate_international_phonenumber


class PhoneNumberField(CharField):
    default_error_messages = {
        'invalid': _('Enter a valid phone number.'),
        }
    default_validators = [validate_international_phonenumber]
    
    def to_python(self, value):
        phone_number = PhoneNumber.to_python(value)
        if phone_number and not phone_number.is_valid():
            raise ValidationError(self.error_messages['invalid'])
        return phone_number
