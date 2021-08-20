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

from django.conf import settings
from django.contrib.auth.models import User

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from instructor.utils import DummyRequest

import boto.s3
from boto.s3.key import Key

from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from student.models import CourseAccessRole, CourseEnrollment, UserProfile


logger = logging.getLogger(__name__)


def do_store_local(tmp_fn, local_dir, local_fn):
    """ handle local storage for generated files
    """
    local_path = local_dir + '/' + local_fn
    if path.exists(local_dir):
        if path.exists(local_path):
            remove(local_path)
        if tmp_fn != local_path:
            copyfile(tmp_fn, local_path)


def do_store_s3(tmp_fn, latest_fn, bucketname):
    """ handle Amazon S3 storage for generated files
    """
    aws_id = settings.AUTH_TOKENS.get('AWS_ID')
    aws_key = settings.AUTH_TOKENS.get('AWS_KEY')
    s3_conn = boto.connect_s3(AWS_ID, AWS_KEY)
    conn_kw = {'aws_access_key_id': aws_id, 'aws_secret_access_key': aws_key}
    bucket = s3_conn.get_bucket(bucketname)
    s3_conn = boto.s3.connect_to_region(bucket.get_location(), **conn_kw)
    bucket = s3_conn.get_bucket(bucketname)
    local_path = tmp_fn
    dest_path = tmp_fn.replace('/tmp/', '')
    try:
        # save timestamped copy
        key = Key(bucket, name=dest_path)
        key.set_contents_from_filename(local_path)
        key = Key(bucket, name=latest_fn)
        key.set_contents_from_filename(local_path)
    except Exception:
        raise
    else:
        logger.info(
            f'uploaded {local_path} to S3 bucket {bucketname}/{dest_path} and replaced {latest_fn}'
        )
        # delete the temp file
        if path.exists(local_path):
            remove(local_path)


def isc_course_participation_report(upload=settings.ISCEDXREPORTS['ISC_COURSE_PARTICIPATION_S3_UPLOAD'],
                                    store_local=settings.ISCEDXREPORTS['ISC_COURSE_PARTICIPATION_STORE_LOCAL']):
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

    dt = str(datetime.now()).replace(' ', '').replace(':', '-')
    fn = '/tmp/isc_course_participation_{0}.csv'.format(dt)
    fp = open(fn, 'w')
    writer = csv.writer(fp, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)

    mongo_courses = modulestore().get_courses()

    writer.writerow([
        'Training Username',
        'User Active/Inactive',
        'Organization',
        'Training Email',
        'Training Name',
        'Job Title',
        'Course Title',
        'Course Id',
        'Course Org',
        'Course Number',
        'Course Run',
        'Course Visibility',
        'Course State',
        'Course Enrollment Date',
        'Course Completion Date',
        'Course Last Section Completed',
        'Course Last Access Date',
        'Grade'
    ])

    # Let's walk through each student profile
    output_data = []
    student_list = User.objects.all()
    for student in student_list:
        for enrollment in student.courseenrollment_set.all():
            if ("/" in str(enrollment.course_id)):
                org = str(enrollment.course_id).split('/')[0].lower()
            elif ("+" in str(enrollment.course_id)):
                org = str(enrollment.course_id).split('+')[0].lower().split(":")[1]
            if org == 'cmc':
                CourseEnrollment.unenroll(student,enrollment.course_id)
                CourseEnrollment.objects.filter(course_id=enrollment.course_id).delete()
                continue
            if not(enrollment.is_active):
                continue
            try:
                if 'beta_testers' in CourseAccessRole.objects.get(
                    user=student, course_id=enrollment.course_id
                ).role:
                    continue
            except Exception:
                pass
            profile = UserProfile.objects.get(user=student.id)
            try:
                job_title = json.loads(profile.meta)['job-title']
            except (KeyError, ValueError):
                job_title = ''
            try:
                organization = json.loads(profile.meta)['organization']
            except (KeyError, ValueError):
                organization = ''
            try:
                full_name = student.profile.name
            except Exception:
                continue
            username = student.username
            active = student.is_active and 'active' or 'inactive'
            email = student.email
            try:
                course = get_course_by_id(enrollment.course_id)
            except Exception:
                continue
            course_name = course.display_name
            visible = False if course.catalog_visibility in ('None', 'About') else True
            staff_only = course.visible_to_staff_only
            course_visibility = 'Public' if (visible and not staff_only) else 'Private'
            course_state = 'Ended' if course.has_ended() else ('Active' if course.has_started() or 'Not started')
            enroll_date = enrollment.created.astimezone(tz.gettz('America/New_York'))
            try:
                completion_date = str(GeneratedCertificate.objects.get(
                    user=student, course_id=enrollment.course_id
                ).created_date.astimezone(tz.gettz('America/New_York')))
            except GeneratedCertificate.DoesNotExist:
                completion_date = 'n/a'
            try:
                smod = StudentModule.objects.filter(
                    student=student, course_id=enrollment.course_id).order_by('-created')[0]
                smod_ch = StudentModule.objects.filter(
                    student=student, course_id=enrollment.course_id, module_type='chapter'
                ).order_by('-created')[0]
                mod = modulestore().get_item(smod.module_state_key)
                last_section_completed = mod.display_name
                last_access_date = smod.created.astimezone(tz.gettz('America/New_York'))
            except (IndexError, ItemNotFoundError):
                last_access_date = 'n/a'
                last_section_completed = 'n/a'
            try:
                course_grade = CourseGradeFactory().create(student, course)
                score = course_grade.percent
            except IndexError:
                score = "0.0"

            output_data = [
                username,
                active,
                organization,
                email,
                full_name,
                job_title,
                course_name,
                str(course.id),
                course.org,
                course.number,
                course.location.run,
                course_visibility,
                course_state,
                str(enroll_date),
                str(completion_date),
                last_section_completed,
                str(last_access_date),
                score
            ]
            encoded_row = [str(s).encode('utf-8') for s in output_data]
            writer.writerow(encoded_row)

    fp.flush()
    fp.close()

    # overwrite latest on local filesystem
    if store_local:
        store_dir = settings.ISCEDXREPORTS['ISC_COURSE_PARTICIPATION_LOCAL_STORAGE_DIR']
        store_fn = 'isc_course_participation.csv'
        do_store_local(fn, store_dir, store_fn)

    # upload to S3 bucket
    if upload:
        latest_fn = 'isc_course_participation.csv'
        bucketname = settings.ISCEDXREPORTS['ISC_COURSE_PARTICIPATION_BUCKET']
        do_store_s3(fn, latest_fn, bucketname)
