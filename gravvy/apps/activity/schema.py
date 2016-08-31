"""
This convenience module defines the set of Verbs for use
with Activity Streams.

Refs:
    http://activitystrea.ms/schema/1.0/
    http://activitystrea.ms/registry/
"""

from django.utils.translation import ugettext_lazy as _

# map each verb to a past tense using a tuple of tuples of 
# (verb_identifier, display_text)
VERB_CHOICES = (
    ('add', _('add')),
    ('delete', _('delete')),
    ('follow', _('start following')),
    ('invite', _('invite')),
    ('leave', _('left')),
    ('like', _('like')),
    ('play', _('play')),
    ('post', _('post')),
    ('share', _('share')), 
    ('stop-following', _('stop following')), 
    ('unlike', _('unlike')), 
    ('unshare', _('unshare')),
    )

# map each verb to a past tense using a tuple of tuples of 
# (verb_identifier, (past_tense,))
#
# Why not just use a tuple of flat tuples?
#     I could achieve the same clarity with flat tuples of form
#     (verb_identifier, past_tense)
#     However this makes things a bit more complex when I try to determine the 
#     valid verbs. With this layout I can easily convert the list to an
#     OrderedDict and get the valid verbs which would be the keys
#     Ex:
#         >>> OrderedDict(VERBS).keys()
VERBS = (
    ('add', (_('added'),)),
    ('delete', (_('deleted'),)),
    ('follow', (_('started following'),)),
    ('invite', (_('invited'),)),
    ('leave', (_('left'),)),
    ('like', (_('liked'),)),
    ('play', (_('played'),)),
    ('post', (_('posted'),)),
    ('share', (_('shared'),)), 
    ('stop-following', (_('stopped following'),)), 
    ('unlike', (_('unliked'),)), 
    ('unshare', (_('unshared'),)),
    )
