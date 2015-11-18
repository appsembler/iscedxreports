"""
Django Celery tasks for ISC edX reporting
"""

from os import environ
import csv
import logging
from datetime import datetime

from django.contrib.auth.models import User
from django.core.mail import EmailMessage

from djcelery import celery

from xmodule.modulestore.django import modulestore
from instructor.utils import DummyRequest
from instructor.views.legacy import get_student_grade_summary_data

from celery.task.schedules import crontab
from celery.decorators import periodic_task

try:
    from iscedxreports.app_settings import CMC_REPORT_RECIPIENTS
except ImportError:
    if environ.get('DJANGO_SETTINGS_MODULE') in (
            'lms.envs.acceptance', 'lms.envs.test',
            'cms.envs.acceptance', 'cms.envs.test'):
        CMC_REPORT_RECIPIENTS = ('bryan@appsembler.com', )


logger = logging.getLogger(__name__)


@periodic_task(run_every=crontab(hour=1, minute=10), name='celery.intersystems.cmc.course_completion')
@celery.task(name='tasks.intersystems.cmc.course_completion')
def cmc_course_completion_report():

    # from celery.contrib import rdb; rdb.set_trace()  # celery remote debugger
    request = DummyRequest()

    fp = open('/tmp/gradeOutputFull.csv', 'w')
    writer = csv.writer(fp, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)

    mongo_courses = modulestore().get_courses()

    writer.writerow(['course_id', 'user_id', 'username', 'full_name', 'email', 'course_access_group', 'final_score'])
    for course in mongo_courses:
        # course_id = 'course-v1:Metalogix+EO301+2015'
        # course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        # course = get_course_by_id(course_key)
        get_raw_scores = False
        datatable = get_student_grade_summary_data(request, course, get_raw_scores=get_raw_scores)
        for d in datatable['data']:
            user_id = d[0]
            user = User.objects.get(id=user_id)
            try:
                course_access_group = user.courseaccessgroup_set.all()[0].name  # assume there's at least one group and get it
            except:
                course_access_group = 'None'
            output_data = [course.id, d[0], d[1], d[2], d[3], course_access_group, d[len(d)-1]]
            encoded_row = [unicode(s).encode('utf-8') for s in output_data]
            # writer.writerow(output_data)
            writer.writerow(encoded_row)

    fp.close()
    
    # email it to specified recipients
    try:
        fp = open('/tmp/gradeOutputFull.csv', 'r')
        fp.seek(0)
        dest_addr = CMC_REPORT_RECIPIENTS
        subject = "Nightly CMC course completion status for {0}".format(str(datetime.now()))
        message = "See attached CSV file"
        mail = EmailMessage(subject, message, to=[dest_addr])
        mail.attach(fp.name, fp.read(), 'text/csv')
        mail.send()
    except:
        logger.warn('CMC Nightly course completion report failed')
    finally:
        fp.close()
