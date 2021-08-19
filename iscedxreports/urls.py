from django.conf import settings
from django.conf.urls import url

from iscedxreports import views


urlpatterns = [
    url(
        r'^courses/{}/feedback$'.format(settings.COURSE_ID_PATTERN),
        views.course_feedback_tab_view, name='course_feedback_tab_view'
    ),
]
