# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from xmodule.modulestore.django import modulestore


def enable_auto_certificate_generation(apps, schema_editor):
    """ enable student-generated certificates on all courses
        by setting the enabled bit
    """
    CertificateGenerationCourseSetting = apps.get_model("certificates", "CertificateGenerationCourseSetting")
    courses = modulestore().get_courses()
    for course in courses:
        key = course.course_key
        ccs, created = CertificateGenerationCourseSetting.objects.get_or_create(course_key=key, enabled=1)
        if not created:
        	ccs.enabled = 1
        	ccs.save()


class Migration(migrations.Migration):

    dependencies = [
        ('iscedxreports', '0003_auto_20160327_2004'),
    ]

    operations = [
        migrations.RunPython(enable_auto_certificate_generation),
    ]
