"""
Customizations to rest_framework.views
"""
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_text

import markdown
from rest_framework.utils import formatting

def apply_markdown(text):
    """
    Simple wrapper around :func:`markdown.markdown` to set the base level
    of '#' style headers to <h2>.
    """
    extensions = ['headerid(level=2)', 'tables', 'fenced_code']
    safe_mode = False
    md = markdown.Markdown(extensions=extensions, safe_mode=safe_mode)
    return md.convert(text)


def markup_description(description):
    """
    Apply HTML markup to the given description.
    """
    description = apply_markdown(description)
    return mark_safe(description)


def get_view_description(view_cls, html=False):
    """
    Given a view class, return a textual description to represent the view.
    This name is used in the browsable API, and in OPTIONS responses.

    This function is the default for the `VIEW_DESCRIPTION_FUNCTION` setting.
    """
    description = view_cls.__doc__ or ''
    description = formatting.dedent(smart_text(description))
    if html:
        return markup_description(description)
    return description
