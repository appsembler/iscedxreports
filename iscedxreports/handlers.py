"""
Signal handlers module for iscedxreports Django app.
"""

# TODO: consider moving these to a compat module for tests.
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.tabs import CourseTab


def add_course_feedback_tab(sender, course_key, **kwargs):
    """Add course feedback tab on course publish.
    We handle the pre_publish signal from xmodule.django.SignalHandler
    and check for a CourseOverview to see if this is a new course.
    We don't want to add back a Feedback tab in case for some reason the
    one we add automatically here is deleted by a Studio user.
    """
    # have to use pre_publish so there's no race condition with the
    # course_published handler that makes a CourseOverview.
    # TODO: consider if there is a better way.
    try:
        CourseOverview.objects.get(id=course_key)
    except CourseOverview.DoesNotExist:
        store = modulestore()
        with store.bulk_operations(course_key):
            course = store.get_course(course_key)
            feedback_tab = CourseTab.load('course_feedback')
            if feedback_tab not in course.tabs:
                course.tabs.append(feedback_tab)
                store.update_item(course, ModuleStoreEnum.UserID.system)
