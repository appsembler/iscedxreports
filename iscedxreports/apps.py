"""
Configuration for iscedxreports Django app
"""

from django.apps import AppConfig

from edxmako import add_lookup
from openedx.core.djangoapps.plugins.constants import (
    ProjectType, SettingsType, PluginURLs, PluginSettings, PluginSignals
)


class ISCEdxReportsConfig(AppConfig):
    """
    Configuration class for iscedxreports Django app.
    It's not just for reports but we're lazy so we're keeping the name.
    """
    name = 'iscedxreports'
    verbose_name = "InterSystems Open edX customizations"

    plugin_app = {

        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: 'iscedxreports',
            }
        },

        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.COMMON: {
                    PluginSettings.RELATIVE_PATH: 'settings.common',
                },
                SettingsType.PRODUCTION: {
                    PluginSettings.RELATIVE_PATH: 'settings.lms_production',
                },
                # SettingsType.DEVSTACK: {
                #     PluginSettings.RELATIVE_PATH: 'settings.devstack',
                # }
            }
            # so far we don't need any CMS app-specific settings
        },

        PluginSignals.CONFIG: {
            ProjectType.CMS: {
                PluginSignals.RELATIVE_PATH: 'handlers',
                PluginSignals.RECEIVERS: [{
                    PluginSignals.RECEIVER_FUNC_NAME: 'add_course_feedback_tab',
                    PluginSignals.SIGNAL_PATH: 'django.db.models.signals.post_save',
                    PluginSignals.SENDER_PATH: 'openedx.core.djangoapps.content.course_overviews.models.CourseOverview',
                }],
            }
        }
    }

    def ready(self):
        add_lookup('main', 'templates', __name__)  # For LMS templates
