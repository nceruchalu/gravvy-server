from django.db import models
from django.core import validators
from django.utils import six
from django.core.exceptions import ValidationError

# imports from containing package: phonenumber_field
from phonenumber import PhoneNumber
from validators import validate_international_phonenumber
import formfields

class PhoneNumberField(models.Field):
    """
    An E.164 Phone Number Field
    """
    
    # allow users of the admin app to see a short description of the field type
    # via the `django.contrib.admindocs` application.
    description = "An E.164 Phone Number"
    
    default_validators = [validate_international_phonenumber]
    
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 16 # 15 digits and '+' sign
        super(PhoneNumberField, self).__init__(*args, **kwargs)
        self.validators.append(validators.MaxLengthValidator(self.max_length))
    
    def deconstruct(self):
        """
        This method tells django how to take an instance of this feild and
        reduce it to a serialized form - in particular, what arguments to pass
        to __init__() to re-create it.
        """
        name, path, args, kwargs = super(PhoneNumberField, self).deconstruct()
        del kwargs["max_length"]
        return name, path, args, kwargs
    
    def get_internal_type(self):
        return "CharField"
    
    def from_db_value(self, value, expression, connection, context):
        """
        Called in all circumstances when the phone number data is loaded from
        the database, including in aggregates and values() calls.
        
        Since we're handling a custom Python type, the PhoneNumber class, we 
        need to make sure that when django initializes an instance of our model 
        and assigns a database value to our custom field attribute, we convert 
        that value into the appropriate Python object.
        
        Args:
            value: a string representation of a phone number since this field
                uses CharField as its internal type
    
        Returns:
            A PhoneNumber class instance
        """
        if value is None:
            return value
        return self.to_python(value)
    
    def to_python(self, value):
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
        phone_number = PhoneNumber.to_python(value)
        
        if phone_number and not phone_number.is_valid():
            raise ValidationError("Invalid input for a PhoneNumber instance")
        return phone_number
    
    def get_prep_value(self, value):
        """
        Generate field's value prepared for saving into a database.
        
        Since using a database requires conversion in both ways, if you override
        `to_python()` you also have to override `get_prep_value()` to convert
        python objects back to query values.
        
        Args:
            value: an instance of PhoneNumber
    
        Returns:
            A string type since this field uses CharField as its internal type.
        """
        if value is None or value == '':
            phone_number_obj = PhoneNumber.to_python(self.default)
            if phone_number_obj:
                return phone_number_object.as_e164
            else:
                return ''

        value = PhoneNumber.to_python(value)
        if isinstance(value, six.string_types):
            # it is an invalid phone number
            return value
        return value.as_e164
    
    def formfield(self, **kwargs):
        """
        Customize the form field used by ModelForm.
        """
        # This is a fairly standard way to set up some defaults
        # while letting the caller override them.
        defaults = {'form_class': formfields.PhoneNumberField}
        defaults.update(kwargs)
        return super(PhoneNumberField, self).formfield(**defaults)
    
    def value_to_string(self, obj):
        """
        Returns a string value of this field from the passed obj.
        This is used by the serialization framework.
        
        Args:
            obj: an instance of model object this attribute is in
    
        Returns:
            An E.164 string representation of phone number object
        """
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)
    
    def pre_save(self, model_instance, add):
        """
        Since SubfieldBase has been removed, ensure to_python() is always
        called on assignment
        
        Args:
            model_instance: the instance this field belongs to
            add: If this instance is being saved to the db for the first time
             
        Returns:
            Value of the appropriate PhoneNumber object
        """
        value = super(PhoneNumberField, self).pre_save(model_instance, add)
        value = self.to_python(value)
        setattr(model_instance, self.attname, value)
        return value
