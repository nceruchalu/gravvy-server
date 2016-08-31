from rest_framework import permissions, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from push_notifications.models import APNSDevice

from gravvy.apps.push.serializers import APNSDeviceSerializer

# Create your views here.
# Create your views here.
@api_view(('GET',))
def push_root(request, format=None):
    return Response({
            'register APNS device token': reverse(
                'push_register_apns', request=request, format=format),
            })


class RegisterAPNSDevice(generics.CreateAPIView):
    """
    Register an APNS Device Token to a given user. Or update user associated 
    with a given APNS Device Token.
    
    ## Reading
    You can't read using this endpoint.
    
    
    ## Publishing
    ### Permissions
    * Only authenticated users can __POST__ using this endpoint.
    
    ### Fields
    Parameter          | Description                             | Type
    ------------------ | --------------------------------------- | --------
    `registration_id`  | Device Token (no hyphens). **Required** | _UUID string_
    `name`             | A device name                           | _string_
    
    A sample `registration_id` is: `740f4707bebcf74f9b7c25d48e3358945f6aa01da5ddb387462c7eaf61bb78ad`
    
    ### Response
    If registration is successful, an APNS device object, otherwise an error 
    message. 
    The APNS device object has the following fields:
    
    ### Fields
    Parameter           | Description                            | Type
    ------------------- | -------------------------------------- | --------
    `user`              | The associated device's user           | _User object_
    `name`              | The registered device's name           | _string_
    `registration_id`   | APNS Device Token. **Required**        | _UUID string_
    `active`            | Indicator that device will be messaged | _boolean_
    `date_created`      | The registration date                  | _date/time_

    
    ## Deleting
    You can't delete using this endpoint
    
    
    ## Updating
    You can't update using this endpoint
    
    ## Endpoints
    Name                            | Description                       
    ------------------------------- | ----------------------------------------
    [`<registration_id>/`](./740f4707bebcf74f9b7c25d48e3358945f6aa01da5ddb387462c7eaf61bb78ad/) | Unregister an APNS device token
    
    ##
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = APNSDeviceSerializer
    queryset = APNSDevice.objects.all()
