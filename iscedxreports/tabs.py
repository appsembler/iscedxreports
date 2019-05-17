"""
Custom Course Tabs for InterSystems.
"""

from django.conf import settings
from django.utils.translation import ugettext_noop
from xmodule.tabs import CourseTab


class CourseFeedbackTab(CourseTab):
    """
    The representation of the Course Report Issues/Feedback tab.
    """

    type = "course_feedback"
    title = ugettext_noop("Report Issues/Feedback")
    view_name = "course_feedback_tab_view"
    is_dynamic = False
    is_default = True  # doesn't do anything yet but once Studio dynamically supports plugins...
    is_hideable = True
    is_movable = True

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Always enable the tab
        """
        return True
