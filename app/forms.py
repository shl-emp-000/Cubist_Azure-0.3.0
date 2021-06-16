from django import forms
from .models import Firmware
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_file_size(file):
    # 2 MB max file size
    MAX_FILE_SIZE = 2 * 1024 * 1024
    file_size = file.size
    if file_size > MAX_FILE_SIZE:
        raise ValidationError(
            _("Firmware file size can not be bigger than 2 MB!")
        )


class FirmwareFormAdmin(forms.ModelForm):
    file = forms.FileField(label='Firmware file', validators=[validate_file_size])

    class Meta:
        model = Firmware
        fields = ['fw_version', 'hw_compability']
        help_texts = {"fw_version": "Semantic versioning MAJOR.MINOR.PATCH, for example 1.33.2",
        "hw_compability": "Compatible hardware with this firmware. Need to match what can be read from the device!"}