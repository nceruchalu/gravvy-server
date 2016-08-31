from django.core.exceptions import ValidationError
from gravvy.fields.phonenumber_field.phonenumber import PhoneNumber

def validate_international_phonenumber(value):
    phone_number = PhoneNumber.to_python(value)
    if phone_number and not phone_number.is_valid():
        raise ValidationError(u'%s is not a valid phone number' % value)
