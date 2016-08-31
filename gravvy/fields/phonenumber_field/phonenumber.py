"""
The PhoneNumber class is the python representation of the PhoneNumberField.
This is the Python object we want to store in a model's attribute of type
PhoneNumberField.

This class will be returned in PhoneNumberField's to_python method.
"""

import sys

from django.core import validators
from django.conf import settings

import phonenumbers
from phonenumbers.phonenumberutil import (NumberParseException,
    region_code_for_number)

# Snippet from the `six` library to help with Python3 compatibility
if sys.version_info[0] == 3:
    string_types = str
else:
    string_types = basestring


class PhoneNumber(phonenumbers.phonenumber.PhoneNumber):
    """
    An extended version of phonenumbers.phonenumber.PhoneNumber that makes it
    easier to use the class in django.
    """
    
    @classmethod
    def from_string(cls, phone_number, region=None):
        """
        Parse a string and return a corresponding PhoneNumber object.
        Probably preferrable to use to_python over this as that has more checks.
        
        Args:
            phone_number: The number that we are attempting to parse. This can
                contain formatting such as +, (, ) and -, as well as a phone
                number extension. It can also be provided in RFC3966 format.
            region: The region we are expecting the number to be from. This is
                only used if the number being parsed is not written in
                international format. The country_code for the number in this
                case would be stored as that of the default region supplied. If
                the number is guaranteed to start with a '+' followed by the
                Country calling code, then None or UNKNOWN_REGION can be used.
        
        Returns:
            A PhoneNumber class instance
            
        Raises:
            NumberParseException: phone_number string is not considered to be a
                viable phone number or if no default region was supplied and the
                number is not in international format (does not start with +).
                Note that validation of whether the number is actually a valid 
                number for a particular region is not performed. This can be 
                done separately with `is_valid`.
        """
        phone_number_obj = cls()
        phonenumbers.parse(number=phone_number, region=region, 
                           keep_raw_input=True, numobj=phone_number_obj)
        return phone_number_obj
    
    
    @classmethod
    def to_python(cls, value):
        """
        Parse a phone number and return a corresponding PhoneNumber object.
        This method is more robust than from_string as it has more checks
        and handles the exceptions.
        
        Args:
            value: The number that we are attempting to parse. This can be:
                * an instance of PhoneNumber
                * a string representing phone number
                * None (if the field allows null=True)
                * invalid data
    
        Returns:
            A PhoneNumber class instance
        """
        if (not value) or (value in validators.EMPTY_VALUES):
            # phone number not provided
            phone_number_obj = None
            
        elif isinstance(value, string_types):
            # argument is possibly the expected string format
            try:
                phone_number_obj = cls.from_string(phone_number=value)
            except NumberParseException:
                # the string provided is not a valid PhoneNumber.
                phone_number_obj = cls(raw_input=value)
        
        elif isinstance(value, PhoneNumber):
            # argument is already a python object
            phone_number_obj = value
            
        else:
            # we received an invalid argument
            phone_number_obj = None
            
        return phone_number_obj
        

    def __unicode__(self):
        """
        Generate E164 representation of phone number or raw input if it's
        invalid.
        """
        return self.as_e164
        
    def is_valid(self):
        """
        Tests whether the phone number matches a valid pattern.
        Note this doesnt actually verify the number is actually in use, which is
        impossible to tell by just looking a a number itself.
        
        Returns:
            Boolean that indicates whether the number is of a valid pattern.
        """
        return phonenumbers.is_valid_number(self)
    
    @property
    def as_e164(self):
        """
        Generate E164 representation of phone number or raw input if it's
        invalid.
        """
        if self.is_valid():
            return phonenumbers.format_number(
                self, phonenumbers.PhoneNumberFormat.E164)
        else:
            return self.raw_input
    
    @property
    def region_code(self):
        """
        Generate region code of phone number or None if it's invalid.
        """
        code = None
        if self.is_valid():
            code = region_code_for_number(self)
        return code
        
    def __len__(self):
        """
        Length of the object is the number of chars in its E164 representation
        """
        return len(self.as_e164)
    
    def __eq__(self, other):
        """
        Phone numbers are equal if E164 representations are equivalent
        """
        if type(other) == PhoneNumber:
            return self.as_e164 == other.as_e164
        else:
            return False
        
    def __ne__(self, other):
        """
        Phone numbers are not equal if E164 represenations are not equivalent
        """
        return not self.__eq__(other)

