from django.test import TestCase
from .forms import FirmwareFormAdmin
from .models import Firmware
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from io import BytesIO


class FirmwareFormAdminTestCase(TestCase):

    def setUp(self):
        self.testfile = BytesIO(b"some dummy bcode data: \x00\x01")
        self.testfile.name = "fw_file.cyacd2"
        self.filelen = self.testfile.getbuffer().nbytes
    
    def test_firmware_version(self):
        form = FirmwareFormAdmin(data={"fw_version": "0.1.0-beta", "hw_compability": "v4"}, files={"file": SimpleUploadedFile(self.testfile.name, self.testfile.read())})

        self.assertTrue(form.is_valid())
        self.assertEqual("0.1.0-beta", form.cleaned_data["fw_version"])

    def test_firmware_file(self):
        form = FirmwareFormAdmin(data={"fw_version": "0.1.0-beta", "hw_compability": "v4"}, files={"file": SimpleUploadedFile(self.testfile.name, self.testfile.read())})

        self.assertTrue(form.is_valid())
        self.assertEqual(self.testfile.name, form.files["file"].name)
        file = form.files["file"].read()
        self.assertEqual(self.filelen, len(file))

    def test_invalid_form(self):
        form = FirmwareFormAdmin(data={"fw_version": "0.1.0-beta", "hw_compability": "v4"})
        self.assertFalse(form.is_valid())

        form = FirmwareFormAdmin(data={"fw_version": "0.1.0-beta"})
        self.assertFalse(form.is_valid())

        form = FirmwareFormAdmin(data={"hw_compability": "v4"})
        self.assertFalse(form.is_valid())

        form = FirmwareFormAdmin(data={"fw_version": "0.1.0-beta"}, files={"file": SimpleUploadedFile(self.testfile.name, self.testfile.read())})
        self.assertFalse(form.is_valid())

        form = FirmwareFormAdmin(data={"hw_compability": "v4"}, files={"file": SimpleUploadedFile(self.testfile.name, self.testfile.read())})
        self.assertFalse(form.is_valid())

        # fw_version and hw_compability should be a unique pair
        fw1 = Firmware.objects.create(fw_version="1.1.0", hw_compability="v4", date_added=timezone.now(), file_name="fw_file_v1.1.0.cyacd2", file=bytes("file_1.1.0_data",'utf-8'))
        form = FirmwareFormAdmin(data={"fw_version": "1.1.0", "hw_compability": "v4"}, files={"file": SimpleUploadedFile(self.testfile.name, self.testfile.read())})
        self.assertFalse(form.is_valid())
