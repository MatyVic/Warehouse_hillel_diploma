from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    birth_date = models.DateField(blank=True, null=True, verbose_name=_("Birth Date"))
    phone_number = models.CharField(
        max_length=15, blank=True, null=True, verbose_name=_("Phone Number")
    )
