"""
Production settings for iscedxreports Django app in the LMS.
"""


def plugin_settings(settings):
    """Update production, LMS specific settings for iscedxreports.
    """

    ENV_TOKENS = settings.ENV_TOKENS

    settings.ISCEDXREPORTS.update(
        dict(
            ISC_COURSE_PARTICIPATION_STORE_LOCAL=ENV_TOKENS.get(
                'ISC_COURSE_PARTICIPATION_STORE_LOCAL', False),
            ISC_COURSE_PARTICIPATION_LOCAL_STORAGE_DIR=ENV_TOKENS.get(
                'ISC_COURSE_PARTICIPATION_LOCAL_STORAGE_DIR', '/tmp')
        )
    )
