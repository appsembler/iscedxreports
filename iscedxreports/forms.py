from django.forms import ModelForm, CharField

from microsite_configuration import microsite

from .models import InterSystemsUserProfile


class InterSystemsUserProfileExtensionForm(ModelForm):

    # b/c of the way the registration extra fields code works,
    # must explicitly specify CharField
    organization = CharField(label='Organization')
    job_title = CharField(label='Job Title')

    def __init__(self, *args, **kwargs):
        super(InterSystemsUserProfileExtensionForm, self).__init__(*args, **kwargs)
        self.fields['organization'].error_messages = {
            "required": u"Please indicate your organization.",
        }
        self.fields['job_title'].error_messages = {
            "required": u"Please indicate your job title.",
        }

        micro = microsite.is_request_in_microsite()
        if not micro or micro and 'job_title' not in microsite.get_value('REGISTRATION_EXTRA_FIELDS',[]):
            del(self.fields['job_title'])

    class Meta(object):
        model = InterSystemsUserProfile
        fields = ('organization', 'job_title')
