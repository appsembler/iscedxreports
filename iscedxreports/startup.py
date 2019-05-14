"""
Django initialization.
"""

from edxmako import add_lookup


def run():
    """
    Add our templates to the Django site.
    """
    # Add our mako templates
    add_lookup('main', 'templates', __name__)  # For LMS
