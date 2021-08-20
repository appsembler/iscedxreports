import logging

from django.core.management.base import BaseCommand, CommandError

from iscedxreports.tasks import isc_course_participation_report


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generates a course completion report for ISC'

    def handle(self, *args, **options):
        try:
            isc_course_participation_report()
            self.stdout.write(self.style.NOTICE('Ran ISC course participation report\n'))
        except Exception:
            raise CommandError('Could not complete ISC course participation report\n')
