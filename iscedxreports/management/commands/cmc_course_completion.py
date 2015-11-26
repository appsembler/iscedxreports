from os import environ
import logging

from django.core.management.base import BaseCommand, CommandError

from iscedxreports.tasks import cmc_course_completion_report

try:
    from iscedxreports.app_settings import CMC_REPORT_RECIPIENTS
except ImportError:
    if environ.get('DJANGO_SETTINGS_MODULE') in (
            'lms.envs.acceptance', 'lms.envs.test',
            'cms.envs.acceptance', 'cms.envs.test'):
        CMC_REPORT_RECIPIENTS = ('bryan@appsembler.com', )


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generates and emails a course completion report for CMC microsite'

    def handle(self, *args, **options):
        try:
            cmc_course_completion_report()
            self.stdout.write(self.style.NOTICE('Ran CMC course completion report'))
        except:
            raise CommandError('Could not complete CMC course completion report')
