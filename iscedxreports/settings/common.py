"""
Common Django settings from iscedxreports plugin.
"""


def plugin_settings(settings):

    settings.ISCEDXREPORTS = dict(
        ISC_COURSE_PARTICIPATION_BUCKET=None,
        ISC_COURSE_PARTICIPATION_S3_UPLOAD=False,
        ISC_COURSE_PARTICIPATION_STORE_LOCAL=True,
        ISC_COURSE_PARTICIPATION_LOCAL_STORAGE_DIR='/tmp'
    )
