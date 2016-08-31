"""
Customizations to rest_framework's fields
"""
from rest_framework import fields

class ImageField(fields.ImageField):
    """
    ImageField that actually allows for no content
    
    Ref: https://github.com/tomchristie/django-rest-framework/issues/2494
    """
    def to_internal_value(self, data):
        # if data is None, image field was not uploaded
        if data:
            return super(ImageField, self).to_internal_value(data)
        return data

