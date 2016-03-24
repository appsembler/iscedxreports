from django.contrib.auth.models import User
from django.db import models


class InterSystemsUserProfile(models.Model):
    """User profile fields specific to InterSystems
    """
    user = models.ForeignKey(User, db_index=True, related_name="InterSystemspreferences")
    organization = models.CharField(verbose_name='Organization', blank=False)
    job_title = models.CharField(verbose_name='Job Title', blank=True)
	