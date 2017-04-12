from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

@api_view(('GET',))
def api_root(request, format=None):
    """
    # Overview
    This describes the resources that make up the official Gravvy API v1.
    If you have any problems or requirements please contact 
    [noddy@nnoduka.com](mailto:noddy@nnoduka.com)
    
    
    ## Current Version
    By default, all requests receive v1 version of the API. This is evident as
    indicated by our api path [`http://gravvy.nnoduka.com/api/v1/`](/api/v1/).
    
    
    ## Schema
    All API access is sadly over HTTP (for now!), and accessed through 
    [`http://gravvy.nnoduka.com/api/v1/`](/api/v1/).
    All data is sent and received as JSON.
    
    ```
    $ curl -i http://gravvy.nnoduka.com/api/v1/
    
    HTTP/1.1 200 OK
    Server: nginx
    Date: Wed, 23 Sep 2015 20:43:54 GMT
    Content-Type: application/json
    Transfer-Encoding: chunked
    Connection: keep-alive
    Vary: Accept-Encoding
    Vary: Accept,Cookie
    X-Frame-Options: SAMEORIGIN
    Allow: OPTIONS, GET

    {}
    ```
    
    Blank fields are included as `null` instead of being omitted.
    
    All timestamps are returned in ISO 8601 format:
    ```
    YYYY-MM-DDTHH:MM:SS.FFFFFFZ
    ```
    
    ##
    ### Summary Representations
    When you fetch a list of some resources, the response includes a subset of 
    the attributes for that resource. This is the "summary" representation of 
    that resource. (Some attributes are computationally expensive for the API to
    provide. For performance reasons, the summary representation excludes those
    attributes. To obtain those attributes, fetch the "detailed" 
    representation.)
    
    **Example:** When you get a list of activities you get the summary
    representation of each user, video, clip in the response. 
    Here, we fetch the list of activities for the currently authenticated user
    ```
    GET /api/v1/user/activities/
    ```
    
    ##
    ### Detailed Representations
    When you fetch an individual resource, the resource typically includes all
    attributes for that resource. This is the "detailed" representation of the
    resource. (Note that authorization sometimes influences the amount of detail
    included in the representation, as with viewing a User object's details).
    
    **Example:** When you get an individual user, you get the detailed
    representation of the user. Here we fetch the user 
    [+18005551234](users/+18005551234/)
    ```
    GET /api/v1/users/+18005551234/
    ```
    
    
    ## Parameters
    Many API methods take optional parameters. For GET requests, any parameters
    not specified as a segment in the path can be passed as an HTTP query string
    parameter:
    
    ```
    $ curl -i "http://gravvy.nnoduka.com/api/v1/users/+18005551234/videos/?cursor=cD0yMDE1LTA4LTA4KzA3JTNBMTMlM0ExNS4xMzMxMjUlMkIwMCUzQTAw"
    ```
    
    In this example, the '+18005551234' value is provdied for the ':user' 
    parameter in the path while ':cursor' is passed in the query string.
    
    For `POST`, `PATCH`, `PUT`, and `DELETE` requests, parameters not included
    in the URL should be encoded as JSON with Content-Type of 
    'application/json':
    ```
    $ curl -i -H "Content-Type: application/json" -X POST -d '{"phone_number":"+18005551234", "password":"something"}' http://gravvy.nnoduka.com/api/v1/account/auth/
    ```
    
    
    ## Root Endpoint
    You can issue a `GET` request to the root endpoint to get all the endpoint
    categories that the API supports:
    ```
    $ curl http://gravvy.nnoduka.com/api/v1/
    ```
    
    
    ## Client Errors
    There are five possible types of client errors on API calls that receive
    request bodies:
       
    **1.** Sending invalid JSON will result in a `400 Bad Request` response.
    ```
    HTTP 400 Bad Request
    Content-Type: application/json
    Vary: Accept
    Allow: GET, PUT, PATCH, HEAD, OPTIONS
    
    {
        "detail": "JSON parse error - No JSON object could be decoded"
    }
    ```
    
    **2.** Sending the wrong type of JSON values will result in a 
          `400 Bad Request` response.
    ```
    HTTP 400 Bad Request
    Content-Type: application/json
    Vary: Accept
    Allow: GET, PUT, PATCH, HEAD, OPTIONS
    
    {
        "full_name": [
            "This field may not be null."
        ]
    }
    ```
    
    **3.** Sending unauthenticated requests will result in a `401 Unauthorized`
           response.
    ```
    HTTP 401 Unauthorized
    Content-Type: application/json
    Vary: Accept
    WWW-Authenticate: Token
    Allow: GET, PUT, PATCH, HEAD, OPTIONS
    
    {
        "detail": "Authentication credentials were not provided."
    }
    ```
    
    **4.** Sending unauthroized requests will result in a `403 Forbidden`
           response.
    ```
    HTTP 403 Forbidden
    Content-Type: application/json
    Vary: Accept
    Allow: GET, HEAD, OPTIONS
    
    {
        "detail": "You do not have permission to perform this action."
    }
    ```
       
    **5.** Sending requests for non-existent data will result in a 
           `404 Not Found` response.
    ```
    HTTP 404 Not Found
    Content-Type: application/json
    Vary: Accept
    Allow: GET, PUT, PATCH, HEAD, OPTIONS
    
    {
        "detail": "Not found."
    }
    ```
    
    All error objects have resource and field properties so that your client
    can tell what the problem is.
    
    
    ## HTTP Redirects
    API v1 uses HTTP redirection where appropriate. Clients should assume any
    request may result in a redirection. REceiving an HTTP redirection is _not_
    an error and clients should follow that redirect. Redirect responses will
    have a `Location` header field which contains the URI of the resource to
    which the client should repeat the requests.
    
    Status Code  | Description 
    ------------ | -------------------------------------------------------------
    `301`        | Permanent redirection. The URI you used to make the request 
                 | has been superseded by the one specified in the `Location`
                 | header field. This and all future requests to this resource
                 | should be directed to the new URI.
                 | 
    `302`, `307` | Temporary redirection. The request should be repeated 
                 | verbatim to the URI specified in the `Location` header field
                 | but clients should continue to use the original URI for 
                 | future requests
    
    Other redirection status codes may be used in accordance with the HTTP 1.1
    spec
    
    
    ## HTTP Verbs
    Where possible, API v1 strives to use appropriate HTTP verbs for each 
    action.
    
    Verb     | Description
    -------- | -----------------------------------------------------------------
    `HEAD`   | Issued against any resource to get just the HTTP header info.
    `GET`    | Used for retrieving resources.
    `POST`   | Used for creating resources.
    `PATCH`  | Used for updating resources with partial JSON data. For instance,
             | if a resource has `title` and `description` attributes. A
             | PATCH request may accept one or more of the attributes to update 
             | the resource.
    `PUT`    | Used for replacing resources or collections. This means
             | if you're updating a resource with a PUT then all fields must be
             | specified.
    `DELETE` | Used for deleting resources.
    
    
    ## Authentication
    There are three ways to authenticate through the API v1. Requests that
    require authentication will return `401 Unauthorized`. if the user isn't
    authenticated. If the user is authenticated but not authorized for the 
    requests some will return `404 Not Found`, instead of `403 Forbidden`, in 
    some places. This is to prevent the accidental leakage of private info
    to unauthorized users.
    
    ### Token Authentication (sent in a header)
    ```
    curl -H "Authorization: Token e60a3051b524b7ca36de52270bc6ac3ef0e33a65" -H "Content-Type: application/json" -d '{"full_name":"Hello"}' -X PATCH https://gravvy.nnoduka.com/v1/user/
    ```
    
    
    ## Hypermedia
    All resources may have one or more `*_url` properties linking to other
    resources. These are meant to provide explicit URLs so that proper API 
    clients don't need to construct URLs on their own. It is highly recommended
    that API clients use these. Doing so will make future upgrades of the API
    easier for developers.
    
    
    ## Pagination
    Requests that return multiple items will be paginated by default. You
    can specify further pages with the `?page` parameter for page-number
    paginated lists, or with the `?cursor` parameter for cursor paginated lists.
    
    ##
    ### Page Number Pagination 
    This pagination style accepts a single 1-indexed page number in the request
    query parameters
    
    **Example Request:**
    ```
    $ curl -i "http://gravvy.nnoduka.com/api/v1/user/videos/?page=4"
    ```
    
    **Response:**
    ```
    HTTP 200 OK
    
    {
        "count": 1023
        "next": "http://gravvy.nnoduka.com/api/v1/user/videos/?page=5",
        "previous": "http://gravvy.nnoduka.com/api/v1/user/videos/?page=3",
        "results": [
            ...
        ]
    }
    ```
    
    ##
    ### Cursor Pagination
    The cursor-based pagination presents an opaque "cursor" indicator that the
    client may use to page through the result set. This pagination style only
    presents forward and reverse controls, and does not allow the client to 
    naviagate to arbitrary positions. 
    
    Cursor based pagination is more complex than other schemes. It also requires
    that the result set presents a fixed ordering, and does not allow the client
    to arbitrarily index into the result set. However it does provide the 
    following benefits:
    
    * Provides a consistent pagination view. It ensures that the client will 
      never see the same item twice when paging through records, even when new 
      items are being inserted by other clients during the pagination process.
    * Supports usage with very large datasets. With extremely large datasets
      pagination using offset-based pagination styles may become inefficient or 
      unusable. Cursor based pagination schemes instead have fixed-time 
      properties, and do not slow down as the dataset size increases.
    
    For more technical details on cursor pagination, see the 
    ["Building cursors for the Disqus API"](http://cramer.io/2011/03/08/building-cursors-for-the-disqus-api) blog post.
    
      
    **Example Request:**
    ```
    $ curl -i "http://gravvy.nnoduka.com/api/v1/user/activities/?cursor=cD0yMDE1LTA4LTA4KzA3JTNBMTMlM0ExNS4xMzMxMjUlMkIwMCUzQTAw
    ```
    
    **Response:**
    ```
    HTTP 200 OK

    {
        "next": "http://gravvy.nnoduka.com/api/v1/user/activities/?cursor=cD0yMDE1LTA4LTA3KzA1JTNBNTMlM0EzNS40MTM0MjQlMkIwMCUzQTAw",
        "previous": "http://gravvy.nnoduka.com/api/v1/user/activities/?cursor=cD0yMDE1LTA4LTA4KzA3JTNBMTMlM0EwNS42NDQ1MTAlMkIwMCUzQTAwJnI9MQ%3D%3D",
        "results": [
            ...
        ]
    }
    ```
    
    ##
    """
    return Response({
            'account root': reverse('account_root', request=request, 
                                    format=format),
            'authenticated user': reverse('user-auth-detail', request=request, 
                                          format=format),
            'users': reverse('user-list', request=request, format=format),
            'videos': reverse('video-list', request=request, format=format),
            'feedbacks': reverse('feedback-list', request=request, 
                                 format=format),
            'push root': reverse('push_root', request=request, format=format),
            })
