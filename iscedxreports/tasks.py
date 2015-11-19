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

from student.models import CourseEnrollment
from courseware.models import StudentModule
from certificates.models import GeneratedCertificate

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

    fp = open('/tmp/cmc_course_completion.csv', 'w')
    writer = csv.writer(fp, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)

    mongo_courses = modulestore().get_courses()

    # writer.writerow(['username', 'course_id', 'user_id', 'username', 'full_name', 'course_access_group', 'final_score'])
    writer.writerow(['Training/CMC Username', 'Training Email', 'Training Name', 'Job Title', 'Course Title', 'Course Selection', 'Completion Date', 'Last Section Completed'])
    for course in mongo_courses:
        if course.org != 'cmc':
            continue
        get_raw_scores = False
        datatable = get_student_grade_summary_data(request, course, get_raw_scores=get_raw_scores)
        for d in datatable['data']:
            user_id = d[0]
            user = User.objects.get(id=user_id)
            try:
                job_title = user.job-title
            except AttributeError:
                job_title = ''
            enroll_date = CourseEnrollment.objects.get(user=user, course_id=course.id).created
            try:
                # these are all ungraded courses and we are counting anything with a GeneratedCertificate 
                # record here as complete.
                completion_date = str(GeneratedCertificate.objects.get(user=user, course_id=course.id).created_date)
            except GeneratedCertificate.DoesNotExist:
                completion_date = 'n/a'
            try:
                last_section_completed = StudentModule.objects.filter(student=user, course_id=course.id).order_by('-created')[0].module_state_key.block_id
            except IndexError:
                last_section_completed = 'n/a'
            output_data = [d[1], user.email, d[2], job_title, course.display_name, str(enroll_date), str(completion_date), last_section_completed]
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
