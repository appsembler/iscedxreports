from os import environ
import logging

from django.core.management.base import BaseCommand, CommandError

from iscedxreports.tasks import va_enrollment_report

try:
    from iscedxreports.app_settings import VA_ENROLLMENT_REPORT_RECIPIENTS
except ImportError:
    if environ.get('DJANGO_SETTINGS_MODULE') in (
            'lms.envs.acceptance', 'lms.envs.test',
            'cms.envs.acceptance', 'cms.envs.test'):
        VA_ENROLLMENT_REPORT_RECIPIENTS = ('bryan@appsembler.com', )


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generates and emails an enrollment report for VA microsite'

    def handle(self, *args, **options):
        try:
            va_enrollment_report()
            self.stdout.write(self.style.NOTICE('Ran VA enrollment report'))
        except:
            raise CommandError('Could not complete VA enrollment report')
