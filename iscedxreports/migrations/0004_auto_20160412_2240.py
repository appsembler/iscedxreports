# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from xmodule.modulestore.django import modulestore


def enable_auto_certificate_generation(apps, schema_editor):
    """ add an enabled CertificateGenerationConfiguration and
        enable student-generated certificates on all courses
        by setting the enabled bit
    """
    CertificateGenerationConfiguration = apps.get_model("certificates", "CertificateGenerationConfiguration")
    ccg = CertificateGenerationConfiguration(enabled=1)  # configuration model.  just add a new one
    ccg.save()
    
    CertificateGenerationCourseSetting = apps.get_model("certificates", "CertificateGenerationCourseSetting")
    courses = modulestore().get_courses()
    for course in courses:
        key = course.location.course_key
        ccs, created = CertificateGenerationCourseSetting.objects.get_or_create(course_key=key, enabled=1)
        if not created:
        	ccs.enabled = 1
        	ccs.save()


class Migration(migrations.Migration):

    dependencies = [
        ('iscedxreports', '0003_auto_20160327_2004'),
        ('certificates', '0005_auto_20151208_0801'),
    ]

    operations = [
        migrations.RunPython(enable_auto_certificate_generation),
    ]
