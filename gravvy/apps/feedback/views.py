from django.core.mail import EmailMessage
from django.conf import settings

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from gravvy.apps.feedback.models import Feedback
from gravvy.apps.feedback.forms import FeedbackForm
from gravvy.apps.feedback.serializers import FeedbackSerializer

# Create your views here.
class FeedbackList(generics.GenericAPIView):
    """
    Submit feedback
    
    ## Reading
    You can't read using this endpoint.
    
    
    ## Publishing
    ### Permissions
    * Authenticated users only
    
    ### Fields
    Parameter  | Description                        | Type
    ---------- | ---------------------------------- | ---------- 
    `body`     | feedback body                      | _string_
        
    ### Response
    If successful, **_true_**, else an error message.
    
    
    ## Deleting
    You can't delete using this endpoint.
    
    
    ## Updating
    You can't update using this endpoint
    
    """
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            # Create FeedbackForm with the serializer
            feedback_form = FeedbackForm(data=serializer.data)
            
            if feedback_form.is_valid():
                cd = feedback_form.cleaned_data
                body = cd['body']
                user = self.request.user
                
                # create and save feedback instance
                feedback = Feedback(body=body, user=user)
                feedback.save()
                                
                # email admins
                message = "User: %s\n\nMessage:\n%s" % (
                    user.get_full_name(), body)
                subject = "Email from Gravvy feedback form"
                email = EmailMessage(subject, message, 
                                     settings.DEFAULT_FROM_EMAIL,
                                     [settings.FEEDBACK_CONTACT_EMAIL])
                email.send(fail_silently=True)
                
                # Return the success message with OK HTTP status
                return Response({'detail':True})
            
            else:
                return Response(feedback_form.errors, 
                                status=status.HTTP_400_BAD_REQUEST)
        
        # coming this far means there likely was a problem
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

