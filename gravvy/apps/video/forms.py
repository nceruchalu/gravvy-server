from django import forms
from django.conf import settings

from gravvy.utils import human_readable_size
from gravvy.fields.phonenumber_field.formfields import PhoneNumberField
from gravvy.apps.account.models import User

class UploadClipForm(forms.Form):
    """
    Form for uploading a video clip
    """
    name = forms.CharField(max_length=30, required=False, initial="")
    number = forms.CharField(initial="")
    formatted_number = PhoneNumberField()
    clip = forms.FileField()
    
    def clean_formatted_number(self):
        number = self.cleaned_data['formatted_number']
        
        # Ensure this user doesn't already have the app
        try:
            user = User.objects.get(phone_number=number)
            if user.is_active:
                raise forms.ValidationError(
                    "You already have the app. So ask the owner for an invite "
                    "and upload clips through the app")
        except User.DoesNotExist:
            pass
        
        return number
        
    def clean_clip(self):
        vidfile = self.cleaned_data['clip']
        
        if vidfile.size > settings.MAX_VIDEO_CLIP_SIZE:
            raise forms.ValidationError(
                "Ensure this file's size is at most %s (it is %s)."
                % (human_readable_size(settings.MAX_VIDEO_CLIP_SIZE), 
                   human_readable_size(vidfile.size)))
        
        if (hasattr(vidfile, 'content_type') and 
            ('video/' not in vidfile.content_type)):
                raise forms.ValidationError(
                    "Upload a valid video file. Detected file type: %s" 
                    % vidfile.content_type)
        
        return vidfile
    
