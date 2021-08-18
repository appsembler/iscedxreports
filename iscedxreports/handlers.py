"""
Signal handlers module for iscedxreports Django app.
"""

# TODO: consider moving these to a compat module for tests.
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.tabs import CourseTab


def add_course_feedback_tab(sender, instance, **kwargs):
    """Add course feedback tab on course creation.
    We handle the post_save signal on CourseOverview and check that
    created and modified datetimes are equal to decide whether this is a new course.
    We don't want to add back a Feedback tab in case for some reason the
    one we add automatically here is deleted by a Studio user.
    """
    is_new_course = True if instance.created == instance.modified else False
    if is_new_course:
        course = CourseOverview.load_from_module_store(instance.id)
        feedback_tab = CourseTab.load('course_feedback')
        if feedback_tab not in course.tabs:
            course.tabs.append(feedback_tab)
