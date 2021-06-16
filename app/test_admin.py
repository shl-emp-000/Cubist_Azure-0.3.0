from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
from datetime import timedelta
from .admin import FirmwareAdmin
from .forms import FirmwareFormAdmin
from .models import Firmware
from io import BytesIO

class MockRequest(object):
    def __init__(self, user=None, form=None):
        self.user = user
        self.FILES = form.files

class FirmwareAdminTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.super_user = User.objects.create_superuser(username='super', email='super@email.org', password='pass')

    def setUp(self):
        self.testfile = BytesIO(b"some dummy bcode data: \x00\x01")
        self.testfile.name = "fw_file.cyacd2"
        self.filelen = self.testfile.getbuffer().nbytes

    
    def test_save_model(self):
        uploaded_file = InMemoryUploadedFile(self.testfile, field_name='file', name=self.testfile.name, size=self.filelen, content_type='file', charset='utf8')
        form = FirmwareFormAdmin(data={"fw_version": "0.1.0-beta", "hw_compability": "v5"}, files={"file": uploaded_file})
        my_model_admin = FirmwareAdmin(model=Firmware, admin_site=AdminSite())
        my_model_admin.save_model(obj=Firmware(), request=MockRequest(user=self.super_user, form=form), form=form, change=None)

        now = timezone.now()
        fw_obj = Firmware.objects.get(fw_version="0.1.0-beta")
        self.assertEqual("0.1.0-beta", fw_obj.fw_version)
        self.assertEqual("v5", fw_obj.hw_compability)
        self.assertEqual(self.testfile.name, fw_obj.file_name)
        self.assertEqual(self.filelen, len(fw_obj.file))
        self.assertTrue((now - timedelta(minutes=2)) < fw_obj.date_added)
    

    def test_save_model_changed(self):
        uploaded_file = InMemoryUploadedFile(self.testfile, field_name='file', name=self.testfile.name, size=self.filelen, content_type='file', charset='utf8')
        form = FirmwareFormAdmin(data={"fw_version": "0.1.0-beta", "hw_compability": "v5"}, files={"file": uploaded_file})
        my_model_admin = FirmwareAdmin(model=Firmware, admin_site=AdminSite())
        my_model_admin.save_model(obj=Firmware(), request=MockRequest(user=self.super_user, form=form), form=form, change=None)

        firmwares = Firmware.objects.all()
        self.assertEqual(1, len(firmwares))
        self.assertEqual("0.1.0-beta", firmwares.first().fw_version)
        self.assertEqual("v5", firmwares.first().hw_compability)

        #form.changed_data = {"fw_version": "0.1.0"}
        change_form = FirmwareFormAdmin(data={"fw_version": "0.1.0", "hw_compability": "v5"}, files={"file": uploaded_file}, initial={"fw_version": "0.1.0-beta"})
        #change_form.changed_data = {"fw_version": "0.1.0"}
        my_model_admin.save_model(obj=Firmware.objects.get(id=1), request=MockRequest(user=self.super_user, form=change_form), form=change_form, change=True)

        firmwares = Firmware.objects.all()
        self.assertEqual(1, len(firmwares))
        self.assertEqual("0.1.0", firmwares.first().fw_version)
        self.assertEqual("v5", firmwares.first().hw_compability)
    

    def test_save_model_invalid_form(self):
        uploaded_file = InMemoryUploadedFile(self.testfile, field_name='file', name=self.testfile.name, size=self.filelen, content_type='file', charset='utf8')
        form = FirmwareFormAdmin(files={"file": uploaded_file})
        my_model_admin = FirmwareAdmin(model=Firmware, admin_site=AdminSite())
        my_model_admin.save_model(obj=Firmware(), request=MockRequest(form=form), form=form, change=None)

        self.assertFalse(form.is_valid())
        with self.assertRaises(Firmware.DoesNotExist):
            Firmware.objects.get(fw_version="0.1.0-beta")

        form = FirmwareFormAdmin(data={"fw_version": "0.1.0-beta"})
        my_model_admin.save_model(obj=Firmware(), request=MockRequest(form=form), form=form, change=None)

        self.assertFalse(form.is_valid())
        with self.assertRaises(Firmware.DoesNotExist):
            Firmware.objects.get(fw_version="0.1.0-beta")
