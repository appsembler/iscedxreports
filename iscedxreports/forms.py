from django.forms import ModelForm, CharField

from .models import InterSystemsUserProfile


class InterSystemsUserProfileExtensionForm(ModelForm):

    # b/c of the way the registration extra fields code works,
    # must explicitly specify CharField
    organization = CharField(label='Organization')

    def __init__(self, *args, **kwargs):
        super(InterSystemsUserProfileExtensionForm, self).__init__(*args, **kwargs)
        self.fields['organization'].error_messages = {
            "required": "Please indicate your organization.",
        }

    class Meta(object):
        model = InterSystemsUserProfile
        fields = ('organization', )
