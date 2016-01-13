from os import environ

from django.conf import settings

try:
    ENV_TOKENS = settings.ENV_TOKENS

    INTERSYSTEMS_REPORT_RECIPIENTS = ENV_TOKENS.get('INTERSYSTEMS_REPORT_RECIPIENTS', None)
    CMC_REPORT_RECIPIENTS = ENV_TOKENS.get('CMC_REPORT_RECIPIENTS', ('bryan@appsembler.com', ))
    VA_ENROLLMENT_REPORT_RECIPIENTS = ENV_TOKENS.get('VA_ENROLLMENT_REPORT_RECIPIENTS', ('bryan@appsembler.com', ))
    ISC_COURSE_PARTICIPATION_REPORT_RECIPIENTS = ENV_TOKENS.get('ISC_COURSE_PARTICIPATION_REPORT_RECIPIENTS', ('bryan@appsembler.com', ))

except AttributeError:
    # these won't be available in test
    if environ.get('DJANGO_SETTINGS_MODULE') in (
            'lms.envs.acceptance', 'lms.envs.test',
            'cms.envs.acceptance', 'cms.envs.test'):
        pass
    else:
        raise
