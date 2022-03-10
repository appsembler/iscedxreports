from datetime import datetime

from django.conf import settings
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie

from courseware.courses import get_studio_url, get_course_with_access
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def course_feedback_tab_view(request, course_id):
    """
    Display the Course Report Issues/Feedback tab
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, 'load', course_key, depth=None,
                                    check_if_enrolled=True)

    context = {
        'course': course,
        'email_addr': configuration_helpers.get_value('DEFAULT_FEEDBACK_EMAIL',
                                                      getattr(settings, 'DEFAULT_FEEDBACK_EMAIL')),
        'email_subj': "Feedback about {} ({})".format(course_id, str(datetime.now())),
        'studio_url': get_studio_url(course, 'course_info')
    }
    return render_to_response('iscedxreports/course_feedback.html', context)
