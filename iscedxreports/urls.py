from django.conf import settings
from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(
        r'^courses/{}/feedback$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'iscedxreports.views.course_feedback_tab_view',
        name='course_feedback_tab_view',
    ),
)
