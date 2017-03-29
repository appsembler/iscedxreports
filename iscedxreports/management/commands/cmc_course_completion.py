from os import environ
import logging

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMessage

from django.conf import settings

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
        except Exception as e:
            self.notify_error(e)
            raise CommandError('Could not complete CMC course completion report')

    def notify_error(self, error):
        dest_addr = settings.ENV_TOKENS.get("TECH_SUPPORT_EMAIL", "support+intersystems@appsembler.com")
        subject = "CMC course completion report failed"
        message = "CMC course completion report failed with error {}".format(error.message)
        mail = EmailMessage(subject, message, to=(dest_addr,))
        mail.send()
