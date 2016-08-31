"""
Utility functions associated with the activity app

Table of Contents:
    - activity_handler: create activity instance on triggered by signal call
"""

def activity_handler(sender, **kwargs):
    """
    Receiver function for activity signal. This callback creates an
    Activity object instance. This would also be a good place to possibly
    publish the activity stream object to a realtime channel if we had such
    functionality built-in.
    
    Args:
        sender: signal sender
        **kwargs: all keyword arguments
        
    Returns:      
        None
    """
    # Avoid circular imports
    from gravvy.apps.activity.models import Activity
    
    kwargs.pop('signal', None)
    
    actor = sender
    verb = kwargs.pop('verb')
    object = kwargs.pop('object', None) 
    target = kwargs.pop('target', None)
    
    # Go through these hoops to ensure the database is only hit once
    if not object and not target:
        act = Activity.objects.create(actor=actor, verb=verb)
    elif not object and target:
        act = Activity.objects.create(actor=actor, verb=verb, target=target)
    elif object and not target:
        act = Activity.objects.create(actor=actor, verb=verb, object=object)
    else:
        act = Activity.objects.create(actor=actor, verb=verb, 
                                      object=object, target=target)
