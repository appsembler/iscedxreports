from django.conf.urls import patterns, url

from .views import InterSystemsUserProfileView


USERNAME_PATTERN = r'(?P<username>[\w.+-]+)'


urlpatterns = [
    url(r'^cmc_course_completion$', 'iscedxreports.views.cmc_course_completion_report'),
]


urlpatterns += patterns(
    '',
    url(
        r'^api/user/v1/intersystemsprofile/' + USERNAME_PATTERN + '$',
        InterSystemsUserProfileView.as_view(),
        name="intersystemsuserprofile_api"
    ),
)