from os import environ
import logging

from django.core.management.base import BaseCommand, CommandError

from iscedxreports.tasks import isc_course_participation_report

try:
    from iscedxreports.app_settings import ISC_COURSE_PARTICIPATION_REPORT_RECIPIENTS
except ImportError:
    if environ.get('DJANGO_SETTINGS_MODULE') in (
            'lms.envs.acceptance', 'lms.envs.test',
            'cms.envs.acceptance', 'cms.envs.test'):
        ISC_COURSE_PARTICIPATION_REPORT_RECIPIENTS = ('bryan@appsembler.com', )


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generates and emails a course completion report for ISC'

    def handle(self, *args, **options):
        try:
            isc_course_participation_report()
            self.stdout.write(self.style.NOTICE('Ran ISC course participation report\n'))
        except Exception as e:
            raise CommandError('Could not complete ISC course participation report\n')
