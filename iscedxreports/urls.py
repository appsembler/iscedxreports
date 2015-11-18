from django.conf.urls import url
from django.conf import settings


urlpatterns = [
    url(r'^cmc_course_completion$', 'iscedxreports.views.cmc_course_completion_report'),
]
