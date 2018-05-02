"""
These are called on
ISC prod by cron via mgmt commands.
This module is called tasks b/c once they were going to be
Celery tasks
"""

from os import environ, remove, path
from shutil import copyfile
import json
import csv
import logging
from datetime import datetime
from dateutil import tz

from django.contrib.auth.models import User
from django.core.mail import EmailMessage

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from instructor.utils import DummyRequest

import boto.s3
from boto.s3.key import Key

# guard against errors in case iscedxreports accidentally installed
# as CMS app
try:
    from instructor.views.legacy import get_student_grade_summary_data
except AttributeError:
    logger = logging.getLogger(__name__)
    logger.warn('\n\niscedxreports should not be installed as a CMS app. '
                'Swallowing errors and continuing. Remove from '
                'ADDL_INSTALLED_APPS in cms.env.json\n\n')


from student.models import CourseEnrollment, UserProfile, CourseAccessRole
from courseware.models import StudentModule
from certificates.models import GeneratedCertificate

try:
    from iscedxreports.app_settings import (CMC_REPORT_RECIPIENTS, VA_ENROLLMENT_REPORT_RECIPIENTS,
                                            ISC_COURSE_PARTICIPATION_REPORT_RECIPIENTS,
                                            ISC_COURSE_PARTICIPATION_BUCKET,
                                            ISC_COURSE_PARTICIPATION_S3_UPLOAD,
                                            ISC_COURSE_PARTICIPATION_STORE_LOCAL,
                                            ISC_COURSE_PARTICIPATION_LOCAL_STORAGE_DIR,
                                            ISC_COURSE_COMPLETION_S3_FOLDER,
                                            CMC_COURSE_COMPLETION_BUCKET,
                                            CMC_COURSE_COMPLETION_S3_UPLOAD,
                                            CMC_COURSE_COMPLETION_STORE_LOCAL,
                                            CMC_COURSE_COMPLETION_LOCAL_STORAGE_DIR,
                                            CMC_COURSE_COMPLETION_S3_FOLDER,
                                            AWS_ID, AWS_KEY,
                                            )
except ImportError:
    if environ.get('DJANGO_SETTINGS_MODULE') in (
            'lms.envs.acceptance', 'lms.envs.test',
            'cms.envs.acceptance', 'cms.envs.test'):
        CMC_REPORT_RECIPIENTS = VA_ENROLLMENT_REPORT_RECIPIENTS = \
            ISC_COURSE_PARTICIPATION_REPORT_RECIPIENTS = ('bryan@appsembler.com', )
        ISC_COURSE_PARTICIPATION_S3_UPLOAD = False
        ISC_COURSE_PARTICIPATION_STORE_LOCAL = False

logger = logging.getLogger(__name__)


def do_store_local(tmp_fn, local_dir, local_fn):
    """Handle local storage for generated files."""
    local_path = local_dir + '/' + local_fn
    if path.exists(local_dir):
        if path.exists(local_path):
            remove(local_path)
        if tmp_fn != local_path:
            copyfile(tmp_fn, local_path)


def do_store_s3(tmp_fn, latest_fn, bucketname, s3_path_prefix):
    """Handle Amazon S3 storage for generated files."""
    s3_conn = boto.connect_s3(AWS_ID, AWS_KEY)
    conn_kw = {'aws_access_key_id': AWS_ID, 'aws_secret_access_key': AWS_KEY}
    bucket = s3_conn.get_bucket(bucketname)
    s3_conn = boto.s3.connect_to_region(bucket.get_location(), **conn_kw)
    bucket = s3_conn.get_bucket(bucketname)
    local_path = tmp_fn
    dest_path = s3_path_prefix + tmp_fn.replace('/tmp/', '')
    try:
        # save timestamped copy
        key = Key(bucket, name=dest_path)
        key.set_contents_from_filename(local_path)
        key = Key(bucket, name=latest_fn)
        key.set_contents_from_filename(local_path)
    except:
        raise
    else:
        logger.info("uploaded {local} to S3 bucket {bucketname}/{s3path} and replaced {latestpath}".format(local=local_path, bucketname=bucketname, s3path=dest_path, latestpath=latest_fn))
        # delete the temp file
        if path.exists(local_path):
            remove(local_path)


def isc_course_participation_report(upload=ISC_COURSE_PARTICIPATION_S3_UPLOAD, 
                                    store_local=ISC_COURSE_PARTICIPATION_STORE_LOCAL):
    """
    Generate an Excel-format CSV report with the following fields for
    all users/courses in the system
    edX Username, user active/inactive, organization, email, name
    job title, course title, course id, course state (draft/published/),
    course enrollment date/time, course completion date/time,
    course last section completed, course last access date/time

    set upload to False if you do not want to upload to S3,
    this will also keep temporary files that are created.

    """
    request = DummyRequest()

    dt = str(datetime.now()).replace(' ', '').replace(':' , '-')
    fn = '/tmp/isc_course_participation_{0}.csv'.format(dt)
    fp = open(fn, 'w')
    writer = csv.writer(fp, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)

    mongo_courses = modulestore().get_courses()

    writer.writerow(['Training Username', 'User Active/Inactive',
                     'Organization', 'Training Email', 'Training Name',
                     'Job Title', 'Course Title', 'Course Id', 'Course Org',
                     'Course Number',
                     'Course Run', 'Course Visibility', 'Course State',
                     'Course Enrollment Date', 'Course Completion Date',
                     'Course Last Section Completed', 'Course Last Access Date',
                     'Grade', ])

    for course in mongo_courses:
        datatable = get_student_grade_summary_data(request, course, get_grades=True, get_raw_scores=False)

        # dummy for now
        visible = course.catalog_visibility in ('None', 'About') and False or True
        # course.ispublic is being used in a non-standard way so not reliable as to public visibility
        # public = course.ispublic != False
        staff_only = course.visible_to_staff_only
        course_visibility = (visible and not staff_only) and 'Public' or 'Private'
        course_state = course.has_ended() and 'Ended' or (course.has_started() and 'Active' or 'Not started')

        for d in datatable['data']:

            user_id = d[0]
            user = User.objects.get(id=user_id)

            try:
                enrollment = CourseEnrollment.objects.filter(user_id=user_id, course_id=course.id)[0]
            except CourseEnrollment.DoesNotExist:
                continue
            active = enrollment.is_active and 'active' or 'inactive'
            profile = UserProfile.objects.get(user=user_id)

            # exclude beta-testers...
            try:
                if 'beta_testers' in CourseAccessRole.objects.get(user=user, course_id=course.id).role:
                    continue
            except:
                pass

            try:
                job_title = json.loads(profile.meta)['job-title']
            except (KeyError, ValueError):
                job_title = ''
            try:
                organization = json.loads(profile.meta)['organization']
            except (KeyError, ValueError):
                organization = ''

            enroll_date = enrollment.created.astimezone(tz.gettz('America/New_York'))

            try:
                # these are all ungraded courses and we are counting anything with a GeneratedCertificate
                # record here as complete.
                completion_date = str(GeneratedCertificate.objects.get(user=user, course_id=course.id).created_date.astimezone(tz.gettz('America/New_York')))
            except GeneratedCertificate.DoesNotExist:
                completion_date = 'n/a'
            try:
                smod = StudentModule.objects.filter(student=user, course_id=course.id).order_by('-created')[0]
                # smod_ch = StudentModule.objects.filter(student=user, course_id=course.id, module_type='chapter').order_by('-created')[0]
                mod = modulestore().get_item(smod.module_state_key)
                last_section_completed = mod.display_name
                last_access_date = smod.created.astimezone(tz.gettz('America/New_York'))
            except (IndexError, ItemNotFoundError):
                last_access_date = 'n/a'
                last_section_completed = 'n/a'

            try:
                grade = d[5]
                grade  # pyflakes
            except IndexError:
                # for some reason sometimes a grade isn't calculated.  Use a 0.0 here.
                d.append(0.0)

            output_data = [d[1], active, organization, user.email, d[2], job_title,
                           course.display_name,
                           str(course.id), course.org, course.number, course.location.run,
                           course_visibility, course_state,
                           str(enroll_date), str(completion_date), last_section_completed,
                           str(last_access_date), d[5]]
            encoded_row = [unicode(s).encode('utf-8') for s in output_data]

            # writer.writerow(output_data)
            writer.writerow(encoded_row)

    fp.close()

    # email it to specified recipients
    try:
        fp = open(fn, 'r')
        fp.seek(0)
        dest_addr = ISC_COURSE_PARTICIPATION_REPORT_RECIPIENTS
        subject = "All course participation status for {0}".format(dt)
        message = "See attached CSV file"
        mail = EmailMessage(subject, message, to=dest_addr)
        mail.attach(fp.name, fp.read(), 'text/csv')
        mail.send()
    except:
        logger.warn('All course participation report failed')
    finally:
        fp.close()

    # overwrite latest on local filesystem
    if store_local:
        store_dir = ISC_COURSE_PARTICIPATION_LOCAL_STORAGE_DIR[0]
        store_fn = 'isc_course_participation.csv'
        do_store_local(fn, store_dir, store_fn)

    # upload to S3 bucket
    if upload:
        latest_fn = 'isc_course_participation.csv'
        bucketname = ISC_COURSE_PARTICIPATION_BUCKET
        s3_path_prefix = ISC_COURSE_COMPLETION_S3_FOLDER
        do_store_s3(fn, latest_fn, bucketname, s3_path_prefix)


def cmc_course_completion_report(upload=CMC_COURSE_COMPLETION_S3_UPLOAD,
                                 store_local=CMC_COURSE_COMPLETION_STORE_LOCAL):

    # from celery.contrib import rdb; rdb.set_trace()  # celery remote debugger
    request = DummyRequest()

    dt = str(datetime.now())
    dt_date_only = dt.split(' ')[0].replace('-', '')
    fn = '/tmp/cmc_course_completion_{0}.csv'.format(dt.replace(' ', '').replace(':', '-'))
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
            try:
                organization = json.loads(profile.meta)['organization']
            except (KeyError, ValueError):
                organization = ''

            try:
                enroll_date = CourseEnrollment.objects.get(user=user, course_id=course.id).created
            except ItemNotFoundError:
                continue
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
            except (IndexError, ItemNotFoundError):
                last_section_completed = 'n/a'
            output_data = [d[1], organization, user.email, d[2], job_title, course.display_name, str(enroll_date), str(completion_date), last_section_completed]
            encoded_row = [unicode(s).encode('utf-8') for s in output_data]
            # writer.writerow(output_data)
            writer.writerow(encoded_row)

    fp.close()

    # email it to specified recipients
    try:
        fp = open(fn, 'r')
        fp.seek(0)
        dest_addr = CMC_REPORT_RECIPIENTS
        subject = "Nightly CMC course completion status for {0}".format(dt_date_only)
        message = "See attached CSV file"
        mail = EmailMessage(subject, message, to=dest_addr)
        mail.attach(fp.name, fp.read(), 'text/csv')
        mail.send()
    except:
        logger.warn('CMC Nightly course completion report failed')
    finally:
        fp.close()

    if store_local:
        store_dir = CMC_COURSE_COMPLETION_LOCAL_STORAGE_DIR[0]
        store_fn = 'cmc_course_completion_{}.csv'.format(dt_date_only)
        do_store_local(fn, store_dir, store_fn)

    # upload to S3 bucket
    if upload:
        latest_fn = 'cmc_course_completion_latest.csv'
        bucketname = CMC_COURSE_COMPLETION_BUCKET
        s3_path_prefix = CMC_COURSE_COMPLETION_S3_FOLDER
        do_store_s3(fn, latest_fn, bucketname, s3_path_prefix)
