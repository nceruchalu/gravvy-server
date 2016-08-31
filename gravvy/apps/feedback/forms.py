from django import forms
from gravvy.apps.feedback.models import Feedback

class FeedbackForm(forms.ModelForm):
    """
    Custom feedback submission form with folowing features:
        * form fields are `body` (from Feedback model), and an additional
          `honeypot` field.
        * honepot field label, 'website', was chosen to attract maximum spam.
    """
    
    # use a label that attracts maximum spam, such as 'website'
    honeypot = forms.CharField(max_length=100, label="Website", required=False)
    
    class Meta:
        model = Feedback
        fields = ('body',)
        widgets = {
            'body': forms.Textarea(
                attrs={'cols': 60, 'rows': 10,
                       'placeholder': 'leave your message here'}),
            }
    
    
    def clean_honeypot(self):
        """
        Confirm that honeypot field is indeed empty. 
        If it isn't then this form submission is invalid and likely spam.
        
        Args:
            None
        
        Returns:
            Cleaned honeypot field value
           
        Raises:
            ValidationError: honeypot is filled so you are a bot
        """
        honeypot = self.cleaned_data.get('honeypot', False)
        if honeypot:
            raise forms.ValidationError("You are a bot.")
        
        return honeypot
