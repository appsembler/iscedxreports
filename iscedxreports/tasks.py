"""
Django Celery tasks for ISC edX reporting
"""

from os import environ
import json
import csv
import logging
from datetime import datetime, timedelta
from dateutil import tz

from django.contrib.auth.models import User
from django.core.mail import EmailMessage

from djcelery import celery

from xmodule.modulestore.django import modulestore
from instructor.utils import DummyRequest

# guard against errors in case iscedxreports accidentally installed
# as CMS app
try:
    from instructor.views.legacy import get_student_grade_summary_data
except AttributeError:
    logger = logging.getLogger(__name__)
    logger.warn('\n\niscedxreports should not be installed as a CMS app. '
                'Swallowing errors and continuing. Remove from '
                'ADDL_INSTALLED_APPS in cms.env.json\n\n')

from celery.task.schedules import crontab
from celery.decorators import periodic_task

from student.models import CourseEnrollment, UserProfile, CourseAccessRole
from courseware.models import StudentModule
from certificates.models import GeneratedCertificate

try:
    from iscedxreports.app_settings import CMC_REPORT_RECIPIENTS, VA_ENROLLMENT_REPORT_RECIPIENTS
except ImportError:
    if environ.get('DJANGO_SETTINGS_MODULE') in (
            'lms.envs.acceptance', 'lms.envs.test',
            'cms.envs.acceptance', 'cms.envs.test'):
        CMC_REPORT_RECIPIENTS = VA_ENROLLMENT_REPORT_RECIPIENTS = ('bryan@appsembler.com', )


logger = logging.getLogger(__name__)


@periodic_task(run_every=crontab(hour=1, minute=10), name='periodictask.intersystems.cmc.course_completion')
@celery.task(name='tasks.intersystems.cmc.course_completion')
def cmc_course_completion_report():

    # from celery.contrib import rdb; rdb.set_trace()  # celery remote debugger
    request = DummyRequest()

    dt = str(datetime.now()).replace(' ', '')
    fn = '/tmp/cmc_course_completion_{0}.csv'.format(dt)
    fp = open(fn, 'w')
    writer = csv.writer(fp, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)

    mongo_courses = modulestore().get_courses()

    writer.writerow(['Training/CMC Username', 'Organization', 'Training Email', 'Training Name', 'Job Title', 'Course Title', 'Course Selection', 'Completion Date', 'Last Section Completed'])
    for course in mongo_courses:
        if course.org != 'cmc':
            continue

        get_raw_scores = False
        datatable = get_student_grade_summary_data(request, course, get_raw_scores=get_raw_scores)
        for d in datatable['data']:
            user_id = d[0]
            user = User.objects.get(id=user_id)
            profile = UserProfile.objects.get(user=user_id)

            # exclude beta-testers...
            try:
                if 'beta_testers' in CourseAccessRole.objects.get(user=user, course_id=course.id).role:
                    continue
            except:
                pass
            # and certain users and email domains
            if user.email.lower().split('@')[1] in ('intersystems.com', 'appsembler.com', 'j2interactive.com') or \
                user.email.lower() in ('julia@ehsol.co.uk', 'julia.riley@rmh.nhs.uk', 'bijal.shah@rmh.nhs.uk',
                                       'john.middleton@rmh.nhs.uk', 'jonathan.merefield@gmail.com',
                                       'staff@example.com', 'bryanlandia+cmctest1@gmail.com'):
                continue
            try:
                job_title = json.loads(profile.meta)['job-title']
            except (KeyError, ValueError):
                job_title = ''
            enroll_date = CourseEnrollment.objects.get(user=user, course_id=course.id).created
            try:
                # these are all ungraded courses and we are counting anything with a GeneratedCertificate 
                # record here as complete.
                completion_date = str(GeneratedCertificate.objects.get(user=user, course_id=course.id).created_date)
            except GeneratedCertificate.DoesNotExist:
                completion_date = 'n/a'
            try:
                smod = StudentModule.objects.filter(student=user, course_id=course.id, module_type='chapter').order_by('-created')[0]
                mod = modulestore().get_item(smod.module_state_key)
                last_section_completed = mod.display_name
            except IndexError:
                last_section_completed = 'n/a'
            output_data = [d[1], profile.organization, user.email, d[2], job_title, course.display_name, str(enroll_date), str(completion_date), last_section_completed]
            encoded_row = [unicode(s).encode('utf-8') for s in output_data]
            # writer.writerow(output_data)
            writer.writerow(encoded_row)

    fp.close()

    # email it to specified recipients
    try:
        fp = open(fn, 'r')
        fp.seek(0)
        dest_addr = CMC_REPORT_RECIPIENTS
        subject = "Nightly CMC course completion status for {0}".format(dt)
        message = "See attached CSV file"
        mail = EmailMessage(subject, message, to=dest_addr)
        mail.attach(fp.name, fp.read(), 'text/csv')
        mail.send()
    except:
        logger.warn('CMC Nightly course completion report failed')
    finally:
        fp.close()


@periodic_task(run_every=crontab(hour=1, minute=10), name='periodictask.intersystems.va.enrollment')
@celery.task(name='tasks.intersystems.va.enrollment')
def va_enrollment_report():
    logger.warn('Running VA Learning Path enrollment report')

    dt = str(datetime.now()).replace(' ', '')
    fn = '/tmp/va_enrollment_{0}.csv'.format(dt)
    fp = open(fn, 'w')
    writer = csv.writer(fp, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(['Username', 'Email', 'Name', 'Enrollment Date'])

    # get enrollments within last 24 hours
    startdate = datetime.today() - timedelta(hours=24)
    enrollments = CourseEnrollment.objects.filter(created__gt=startdate).order_by('-created')
    store = modulestore()
    valid_enrollments = 0

    for enroll in enrollments:
        course = store.get_course(enroll.course_id)
        if not course:
            # in case it's been deleted 
            continue

        if course.org != 'va':
            continue

        valid_enrollments += 1
        user = User.objects.get(id=enroll.user_id)
        profile = UserProfile.objects.get(user_id=enroll.user_id)
        created = enroll.created.astimezone(tz.gettz('America/New_York'))
        output_data = [user.username, user.email, profile.name, str(created)]
        encoded_row = [unicode(s).encode('utf-8') for s in output_data]
        
        writer.writerow(encoded_row)

    fp.close()

    # email it to specified recipients
    try:
        fp = open(fn, 'r')
        fp.seek(0)
        dest_addr = VA_ENROLLMENT_REPORT_RECIPIENTS
        subject = "Nightly new VA Learning Path course enrollments status for {0}".format(dt)
        if not valid_enrollments:
            message = "No new enrollments in last 24 hours"
        else:
            message = "See attached CSV file for new enrollments in Learning Path courses in the last 24 hours"
        mail = EmailMessage(subject, message, to=dest_addr)
        if valid_enrollments:
            mail.attach(fp.name, fp.read(), 'text/csv')
        mail.send()
    except:
        logger.warn('VA Learning Path enrollment report failed')
    finally:
        fp.close()
