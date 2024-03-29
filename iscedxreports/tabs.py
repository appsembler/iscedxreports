"""
Custom Course Tabs for InterSystems.
"""

from django.utils.translation import ugettext_noop
from xmodule.tabs import CourseTab


class CourseFeedbackTab(CourseTab):
    """
    The representation of the Course Report Issues/Feedback tab.
    """

    type = "course_feedback"
    title = ugettext_noop("Report Issues/Feedback")
    view_name = "iscedxreports:course_feedback_tab_view"
    is_dynamic = False  # not dynamic, to be able to reorder and hide
    is_default = False  # we add explicitly through a signal handler on course pre_publish
    is_hideable = True
    is_movable = True

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Always enable the tab
        """
        return True
