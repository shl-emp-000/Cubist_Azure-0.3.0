from api.views import DownloadLatestFirmwareViewSet, LatestFirmwareViewSet
from rest_framework import status
from django.urls import reverse
from app.models import Firmware, Device, History
from .serializers import FirmwareVersionSerializer
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase
from io import BytesIO
import jwt
import os


class LatestFirmwareViewSetTest(APITestCase):
    """ Test module for GET latest firmware API """

    def setUp(self):
        now = timezone.now()
        self.hw_rev = "v5"
        self.fw1 = Firmware.objects.create(fw_version="1.1.0", hw_compability=self.hw_rev, date_added=(now - timedelta(days=10)), file_name="fw_file_v1.1.0.cyacd2", file=bytes("file_1.1.0_hw_v5_data",'utf-8'))
        self.fw2 = Firmware.objects.create(fw_version="2.1.0", hw_compability=self.hw_rev, date_added=(now - timedelta(days=5)), file_name="fw_file_v2.1.0.cyacd2", file=bytes("file_2.1.0_hw_v5_data",'utf-8'))
        self.fw3 = Firmware.objects.create(fw_version="3.1.0", hw_compability=self.hw_rev, date_added=(now - timedelta(days=2)), file_name="fw_file_v3.1.0.cyacd2", file=bytes("file_3.1.0_hw_v5_data",'utf-8'))
        # Add more Firmwares with same fw_versions to ensure the hw rev check works
        self.fw4 = Firmware.objects.create(fw_version="1.1.0", hw_compability="v10", date_added=(now - timedelta(days=8)), file_name="fw_file4.cyacd2", file=bytes("file_1.1.0_hw_v10_data",'utf-8'))
        self.fw5 = Firmware.objects.create(fw_version="2.1.0", hw_compability="v10", date_added=(now - timedelta(days=2)), file_name="fw_file5.cyacd2", file=bytes("file_2.1.0_hw_v10_data",'utf-8'))
        self.fw6 = Firmware.objects.create(fw_version="3.1.0", hw_compability="v10", date_added=(now - timedelta(days=1)), file_name="fw_file6.cyacd2", file=bytes("file_3.1.0_hw_v10_data",'utf-8'))
        self.fw7 = Firmware.objects.create(fw_version="1.1.0", hw_compability="v4", date_added=(now - timedelta(days=11)), file_name="fw_file7.cyacd2", file=bytes("file_1.1.0_hw_v4_data",'utf-8'))
        self.fw8 = Firmware.objects.create(fw_version="2.1.0", hw_compability="v4", date_added=(now - timedelta(days=6)), file_name="fw_file8.cyacd2", file=bytes("file_2.1.0_hw_v4_data",'utf-8'))
        self.fw9 = Firmware.objects.create(fw_version="3.1.0", hw_compability="v4", date_added=(now - timedelta(days=3)), file_name="fw_file9.cyacd2", file=bytes("file_3.1.0_hw_v4_data",'utf-8'))
        # initialize the APIClient app
        self.client = APIClient()
        exp_time = now + timedelta(minutes=10)
        self.token = jwt.encode({"jti": 1122, "token_type": "access", "exp": exp_time, "user_id": 54321, "hw_rev": self.hw_rev}, os.environ['SIGNING_KEY'], algorithm="HS256", headers={"typ": "JWT"})

    def test_get_latest_firmware_version_SE02(self):
        ''' Requirement SE-02: Test that authorized client can access endpoint'''
        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.get(reverse('latest_fw_version-list'))
        
        latest_fw = Firmware.objects.get(pk=self.fw3.pk)
        serializer = FirmwareVersionSerializer(latest_fw)

        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_latest_firmware_version_unauthorized_SE02(self):
        ''' Requirement SE-02: Test that unauthorized client cannot access endpoint'''
        response = self.client.get(reverse('latest_fw_version-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_latest_firmware_version_invalid_token_SE02(self):
        ''' Requirement SE-02: Test that unauthorized client cannot access endpoint'''
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + 'badToken')
        response = self.client.get(reverse('latest_fw_version-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_latest_firmware_version_on_empty_model(self):
        Firmware.objects.all().delete()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.get(reverse('latest_fw_version-list'))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_latest_firmware_version_for_hw_rev_with_no_available_fw(self):
        exp_time = timezone.now() + timedelta(minutes=10)
        new_token = jwt.encode({"jti": 1122, "token_type": "access", "exp": exp_time, "user_id": 12345, "hw_rev": "v20"}, os.environ['SIGNING_KEY'], algorithm="HS256", headers={"typ": "JWT"})
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + new_token)
        response = self.client.get(reverse('latest_fw_version-list'))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_hw_rev_from_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.get(reverse('latest_fw_version-list'))
        request = response.wsgi_request
        hw_rev = LatestFirmwareViewSet.get_hw_rev_from_token(self, request)
        self.assertEqual(hw_rev, self.hw_rev)

    def test_get_hw_rev_from_token_none(self):
        exp_time = timezone.now() + timedelta(minutes=10)
        new_token = jwt.encode({"jti": 1122, "token_type": "access", "exp": exp_time, "user_id": 12345}, os.environ['SIGNING_KEY'], algorithm="HS256", headers={"typ": "JWT"})
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + new_token)
        response = self.client.get(reverse('latest_fw_version-list'))
        request = response.wsgi_request
        hw_rev = LatestFirmwareViewSet.get_hw_rev_from_token(self, request)
        self.assertIsNone(hw_rev)

    def test_get_hw_rev_from_token_empty_string(self):
        empty_string = ""
        exp_time = timezone.now() + timedelta(minutes=10)
        new_token = jwt.encode({"jti": 1122, "token_type": "access", "exp": exp_time, "user_id": 12345, "hw_rev": empty_string}, os.environ['SIGNING_KEY'], algorithm="HS256", headers={"typ": "JWT"})
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + new_token)
        response = self.client.get(reverse('latest_fw_version-list'))
        request = response.wsgi_request
        hw_rev = LatestFirmwareViewSet.get_hw_rev_from_token(self, request)
        self.assertIsNone(hw_rev)


class DownloadLatestFirmwareViewSetTest(APITestCase):
    """ Test module for GET download latest firmware API """

    def setUp(self):
        now = timezone.now()
        self.testfile1 = BytesIO(b"some dummy bcode data: \x00\x01")
        self.testfile1.name = "fw_file1.cyacd2"
        self.testfilelen1 = self.testfile1.getbuffer().nbytes

        self.testfile2 = BytesIO(b"some dummy bcode data: \x00\x01\x02")
        self.testfile2.name = "fw_file2.cyacd2"
        self.testfilelen2 = self.testfile2.getbuffer().nbytes

        self.hw_rev = "v5"
        self.fw1 = Firmware.objects.create(fw_version="1.1.0", hw_compability=self.hw_rev, date_added=(now - timedelta(days=10)), file_name="fw_file1.cyacd2", file=self.testfile1.getbuffer())
        self.fw2 = Firmware.objects.create(fw_version="2.1.0", hw_compability=self.hw_rev, date_added=(now - timedelta(days=5)), file_name="fw_file2.cyacd2", file=self.testfile2.getbuffer())
        # Add more Firmwares with same fw_versions to ensure the hw rev check works
        self.fw3 = Firmware.objects.create(fw_version="1.1.0", hw_compability="v10", date_added=(now - timedelta(days=8)), file_name="fw_file3.cyacd2", file=self.testfile1.getbuffer())
        self.fw4 = Firmware.objects.create(fw_version="2.1.0", hw_compability="v10", date_added=(now - timedelta(days=2)), file_name="fw_file4.cyacd2", file=self.testfile2.getbuffer())
        self.fw5 = Firmware.objects.create(fw_version="1.1.0", hw_compability="v4", date_added=(now - timedelta(days=11)), file_name="fw_file5.cyacd2", file=self.testfile1.getbuffer())
        self.fw6 = Firmware.objects.create(fw_version="2.1.0", hw_compability="v4", date_added=(now - timedelta(days=6)), file_name="fw_file6.cyacd2", file=self.testfile2.getbuffer())

        # initialize the APIClient app
        self.client = APIClient()
        exp_time = now + timedelta(minutes=10)
        self.token = jwt.encode({"jti": 1122, "token_type": "access", "exp": exp_time, "user_id": 54321, "hw_rev": self.hw_rev}, os.environ['SIGNING_KEY'], algorithm="HS256", headers={"typ": "JWT"})

    def test_download_latest_firmware_SE02(self):
        ''' Requirement SE-02: Test that authorized client can access endpoint'''
        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.get(reverse('dl_latest_fw-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.get('Content-Disposition'),"attachment; filename=" + self.fw2.fw_version + ".cyacd2")
        try:
            f = BytesIO(response.content)
            self.assertEqual(f.getbuffer().nbytes, self.testfilelen2)
            self.assertEqual(f.getbuffer(), self.testfile2.getbuffer())
        finally:
            f.close()

    def test_download_latest_firmware_unauthorized_SE02(self):
        ''' Requirement SE-02: Test that unauthorized client cannot access endpoint'''
        response = self.client.get(reverse('dl_latest_fw-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_download_latest_firmware_invalid_token_SE02(self):
        ''' Requirement SE-02: Test that unauthorized client cannot access endpoint'''
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + 'badToken')
        response = self.client.get(reverse('dl_latest_fw-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_download_latest_firmware_on_empty_model(self):
        Firmware.objects.all().delete()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.get(reverse('dl_latest_fw-list'))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_download_latest_firmware_for_hw_rev_with_no_available_fw(self):
        exp_time = timezone.now() + timedelta(minutes=10)
        new_token = jwt.encode({"jti": 1122, "token_type": "access", "exp": exp_time, "user_id": 12345, "hw_rev": "v20"}, os.environ['SIGNING_KEY'], algorithm="HS256", headers={"typ": "JWT"})
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + new_token)
        response = self.client.get(reverse('dl_latest_fw-list'))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_hw_rev_from_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.get(reverse('dl_latest_fw-list'))
        request = response.wsgi_request
        hw_rev = DownloadLatestFirmwareViewSet.get_hw_rev_from_token(self, request)
        self.assertEqual(hw_rev, self.hw_rev)

    def test_get_hw_rev_from_token_none(self):
        exp_time = timezone.now() + timedelta(minutes=10)
        new_token = jwt.encode({"jti": 1122, "token_type": "access", "exp": exp_time, "user_id": 12345}, os.environ['SIGNING_KEY'], algorithm="HS256", headers={"typ": "JWT"})
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + new_token)
        response = self.client.get(reverse('dl_latest_fw-list'))
        request = response.wsgi_request
        hw_rev = DownloadLatestFirmwareViewSet.get_hw_rev_from_token(self, request)
        self.assertIsNone(hw_rev)
    
    def test_get_hw_rev_from_token_empty_string(self):
        empty_string = ""
        exp_time = timezone.now() + timedelta(minutes=10)
        new_token = jwt.encode({"jti": 1122, "token_type": "access", "exp": exp_time, "user_id": 12345, "hw_rev": empty_string}, os.environ['SIGNING_KEY'], algorithm="HS256", headers={"typ": "JWT"})
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + new_token)
        response = self.client.get(reverse('dl_latest_fw-list'))
        request = response.wsgi_request
        hw_rev = DownloadLatestFirmwareViewSet.get_hw_rev_from_token(self, request)
        self.assertIsNone(hw_rev)

class PostResultsViewSetTest(APITestCase):
    """ Test module for POST FOTA reuslt API """

    def setUp(self):
        now = timezone.now()
        self.exp_time = timezone.now()
        self.testfile1 = BytesIO(b"some dummy bcode data: \x00\x01")
        self.testfile1.name = "fw_file1.cyacd2"
        self.testfilelen1 = self.testfile1.getbuffer().nbytes

        self.testfile2 = BytesIO(b"some dummy bcode data: \x00\x01\x02")
        self.testfile2.name = "fw_file2.cyacd2"
        self.testfilelen2 = self.testfile2.getbuffer().nbytes

        self.hw_rev = "v5"
        self.fw1 = Firmware.objects.create(fw_version="1.1.0", hw_compability=self.hw_rev, date_added=(now - timedelta(days=10)), file_name="fw_file1.cyacd2", file=self.testfile1.getbuffer())
        self.fw2 = Firmware.objects.create(fw_version="2.1.0", hw_compability=self.hw_rev, date_added=(now - timedelta(days=5)), file_name="fw_file2.cyacd2", file=self.testfile2.getbuffer())
        # Add more Firmwares with same fw_versions to ensure the hw rev check works
        self.fw3 = Firmware.objects.create(fw_version="1.1.0", hw_compability="v10", date_added=(now - timedelta(days=8)), file_name="fw_file3.cyacd2", file=self.testfile1.getbuffer())
        self.fw4 = Firmware.objects.create(fw_version="2.1.0", hw_compability="v10", date_added=(now - timedelta(days=2)), file_name="fw_file4.cyacd2", file=self.testfile2.getbuffer())
        self.fw5 = Firmware.objects.create(fw_version="1.1.0", hw_compability="v4", date_added=(now - timedelta(days=11)), file_name="fw_file5.cyacd2", file=self.testfile1.getbuffer())
        self.fw6 = Firmware.objects.create(fw_version="2.1.0", hw_compability="v4", date_added=(now - timedelta(days=6)), file_name="fw_file6.cyacd2", file=self.testfile2.getbuffer())

        self.dv = Device.objects.create(serial_number="12345", created=(now - timedelta(days=7)), firmware=self.fw1, last_update=None,
        manufacturer_name="ManufacturerName", model_number="ModelNumber", hardware_revision="HWRev", software_revision="SWRev")
        # initialize the APIClient app
        self.client = APIClient()
        exp_time = now + timedelta(minutes=10)
        self.token = jwt.encode({"jti": 1122, "token_type": "access", "exp": exp_time, "user_id": 54321, "hw_rev": self.hw_rev}, os.environ['SIGNING_KEY'], algorithm="HS256", headers={"typ": "JWT"})


    def test_post_results_fota_success_SE02(self):
        ''' Requirement SE-02: Test that authorized client can access endpoint'''
        # Verify device starting data
        self.assertIsNone(self.dv.last_update)
        self.assertEqual(self.dv.firmware, self.fw1)
        self.assertEqual(self.dv.manufacturer_name, "ManufacturerName")
        self.assertEqual(self.dv.model_number, "ModelNumber")
        self.assertEqual(self.dv.hardware_revision, "HWRev")
        self.assertEqual(self.dv.software_revision, "SWRev")

        data = {
            "fw_update_started": str(self.exp_time),
            "device": "12345",
            "fw_update_success": "true",
            "firmware": "2.1.0",
            "device_firmware": "1.1.0",
            "reason": "OK",
            "manufacturer_name": "man name",
            "model_number": "mod numb",
            "hardware_revision": self.hw_rev,
            "software_revision": "sw rev"}

        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.post(reverse('post_results-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Refresh device obj, should have been updated
        self.dv.refresh_from_db()
        # Verify that device was updated
        self.assertEqual(self.dv.last_update, self.exp_time)
        self.assertEqual(self.dv.firmware, self.fw2)
        self.assertEqual(self.dv.manufacturer_name, "man name")
        self.assertEqual(self.dv.model_number, "mod numb")
        self.assertEqual(self.dv.hardware_revision, self.hw_rev)
        self.assertEqual(self.dv.software_revision, "sw rev")

        # Verify that the history instance was created
        history_all = History.objects.all()
        # Should only be one instance
        self.assertEqual(1, len(history_all))
        history = history_all[0]

        self.assertEqual(history.device, self.dv)
        self.assertEqual(history.fw_update_started, self.exp_time)
        self.assertTrue(history.fw_update_success)
        self.assertEqual(history.firmware, self.fw2)
        self.assertEqual(history.device_firmware, str(self.fw1))
        self.assertEqual(history.reason, "OK")
        self.assertEqual(history.manufacturer_name, "man name")
        self.assertEqual(history.model_number, "mod numb")
        self.assertEqual(history.hardware_revision, self.hw_rev)
        self.assertEqual(history.software_revision, "sw rev")


    def test_post_results_fota_success_new_device(self):
        data = {
            "fw_update_started": str(self.exp_time),
            "device": "NewDevice",
            "fw_update_success": "true",
            "firmware": "2.1.0",
            "device_firmware": "1.1.0",
            "reason": "OK",
            "manufacturer_name": "man name",
            "model_number": "mod numb",
            "hardware_revision": self.hw_rev,
            "software_revision": "sw rev"}

        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.post(reverse('post_results-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Should be two devices in db now
        devices = Device.objects.all()
        self.assertEqual(2, len(devices))
        oldDevice = devices.get(serial_number='12345')
        self.assertEqual(self.dv, oldDevice)
        newDevice = devices.get(serial_number='NewDevice')

        # Verify the new device
        self.assertEqual(newDevice.last_update, self.exp_time)
        self.assertEqual(newDevice.firmware, self.fw2)
        self.assertEqual(newDevice.manufacturer_name, "man name")
        self.assertEqual(newDevice.model_number, "mod numb")
        self.assertEqual(newDevice.hardware_revision, self.hw_rev)
        self.assertEqual(newDevice.software_revision, "sw rev")
        self.assertTrue(newDevice.created.isoformat() > newDevice.last_update.isoformat())

        # Verify that the history instance was created
        history_all = History.objects.all()
        # Should only be one instance
        self.assertEqual(1, len(history_all))
        history = history_all[0]

        self.assertEqual(history.device, newDevice)
        self.assertEqual(history.fw_update_started, self.exp_time)
        self.assertTrue(history.fw_update_success)
        self.assertEqual(history.firmware, self.fw2)
        self.assertEqual(history.device_firmware, str(self.fw1))
        self.assertEqual(history.reason, "OK")
        self.assertEqual(history.manufacturer_name, "man name")
        self.assertEqual(history.model_number, "mod numb")
        self.assertEqual(history.hardware_revision, self.hw_rev)
        self.assertEqual(history.software_revision, "sw rev")


    def test_post_results_fota_fail(self):
        # Verify device starting data
        self.assertIsNone(self.dv.last_update)
        self.assertEqual(self.dv.firmware, self.fw1)
        self.assertEqual(self.dv.manufacturer_name, "ManufacturerName")
        self.assertEqual(self.dv.model_number, "ModelNumber")
        self.assertEqual(self.dv.hardware_revision, "HWRev")
        self.assertEqual(self.dv.software_revision, "SWRev")

        data = {
            "fw_update_started": str(self.exp_time),
            "device": "12345",
            "fw_update_success": "false",
            "firmware": "2.1.0",
            "device_firmware": "1.1.0",
            "reason": "Could not update for some reason",
            "manufacturer_name": "man name",
            "model_number": "mod numb",
            "hardware_revision": self.hw_rev,
            "software_revision": "sw rev"}

        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.post(reverse('post_results-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Should still only be one object in db
        devices = Device.objects.all()
        self.assertEqual(1, len(devices))
        # Refresh device obj, should not have been updated
        self.dv.refresh_from_db()
        # Verify that device was not updated
        self.assertIsNone(self.dv.last_update)
        self.assertEqual(self.dv.firmware, self.fw1)
        self.assertEqual(self.dv.manufacturer_name, "ManufacturerName")
        self.assertEqual(self.dv.model_number, "ModelNumber")
        self.assertEqual(self.dv.hardware_revision, "HWRev")
        self.assertEqual(self.dv.software_revision, "SWRev")

        # Verify that the history instance was created
        history_all = History.objects.all()
        # Should only be one instance
        self.assertEqual(1, len(history_all))
        history = history_all[0]

        self.assertEqual(history.device, self.dv)
        self.assertEqual(history.fw_update_started, self.exp_time)
        self.assertFalse(history.fw_update_success)
        self.assertEqual(history.firmware, self.fw2)
        self.assertEqual(history.device_firmware, str(self.fw1))
        self.assertEqual(history.reason, "Could not update for some reason")
        self.assertEqual(history.manufacturer_name, "man name")
        self.assertEqual(history.model_number, "mod numb")
        self.assertEqual(history.hardware_revision, self.hw_rev)
        self.assertEqual(history.software_revision, "sw rev")


    def test_post_results_fota_fail_new_devive(self):
        data = {
            "fw_update_started": str(self.exp_time),
            "device": "NewDevice",
            "fw_update_success": "false",
            "firmware": "2.1.0",
            "device_firmware": "1.1.0",
            "reason": "Could not update for some reason",
            "manufacturer_name": "man name",
            "model_number": "mod numb",
            "hardware_revision": self.hw_rev,
            "software_revision": "sw rev"}

        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.post(reverse('post_results-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Should be two devices in db now
        devices = Device.objects.all()
        self.assertEqual(2, len(devices))
        oldDevice = devices.get(serial_number='12345')
        self.assertEqual(self.dv, oldDevice)
        newDevice = devices.get(serial_number='NewDevice')

        # Verify the new device 
        self.assertIsNone(newDevice.last_update)
        self.assertEqual(newDevice.firmware, self.fw1)
        self.assertEqual(newDevice.manufacturer_name, "man name")
        self.assertEqual(newDevice.model_number, "mod numb")
        self.assertEqual(newDevice.hardware_revision, self.hw_rev)
        self.assertEqual(newDevice.software_revision, "sw rev")

        # Verify that the history instance was created
        history_all = History.objects.all()
        # Should only be one instance
        self.assertEqual(1, len(history_all))
        history = history_all[0]

        self.assertEqual(history.device, newDevice)
        self.assertEqual(history.fw_update_started, self.exp_time)
        self.assertFalse(history.fw_update_success)
        self.assertEqual(history.firmware, self.fw2)
        self.assertEqual(history.device_firmware, str(self.fw1))
        self.assertEqual(history.reason, "Could not update for some reason")
        self.assertEqual(history.manufacturer_name, "man name")
        self.assertEqual(history.model_number, "mod numb")
        self.assertEqual(history.hardware_revision, self.hw_rev)
        self.assertEqual(history.software_revision, "sw rev")


    def test_post_results_fota_success_unknown_device_fw(self):
        data = {
            "fw_update_started": str(self.exp_time),
            "device": "12345",
            "fw_update_success": "true",
            "firmware": "2.1.0",
            "device_firmware": "0.1.0-beta",
            "reason": "OK",
            "manufacturer_name": "man name",
            "model_number": "mod numb",
            "hardware_revision": self.hw_rev,
            "software_revision": "sw rev"}

        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.post(reverse('post_results-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Refresh device obj, should have been updated
        self.dv.refresh_from_db()
        # Verify that device was updated
        self.assertEqual(self.dv.last_update, self.exp_time)
        self.assertEqual(self.dv.firmware, self.fw2)
        self.assertEqual(self.dv.manufacturer_name, "man name")
        self.assertEqual(self.dv.model_number, "mod numb")
        self.assertEqual(self.dv.hardware_revision, self.hw_rev)
        self.assertEqual(self.dv.software_revision, "sw rev")

        # Verify that the history instance was created
        history_all = History.objects.all()
        # Should only be one instance
        self.assertEqual(1, len(history_all))
        history = history_all[0]

        self.assertEqual(history.device, self.dv)
        self.assertEqual(history.fw_update_started, self.exp_time)
        self.assertTrue(history.fw_update_success)
        self.assertEqual(history.firmware, self.fw2)
        self.assertEqual(history.device_firmware, "0.1.0-beta")
        self.assertEqual(history.reason, "OK")
        self.assertEqual(history.manufacturer_name, "man name")
        self.assertEqual(history.model_number, "mod numb")
        self.assertEqual(history.hardware_revision, self.hw_rev)
        self.assertEqual(history.software_revision, "sw rev")


    def test_post_results_unauthorized_SE02(self):
        ''' Requirement SE-02: Test that unauthorized client cannot access endpoint'''
        data = {
            "fw_update_started": str(self.exp_time),
            "device": "NewDevice",
            "fw_update_success": "false",
            "firmware": "2.1.0",
            "device_firmware": "1.1.0",
            "reason": "Could not update for some reason",
            "manufacturer_name": "man name",
            "model_number": "mod numb",
            "hardware_revision": self.hw_rev,
            "software_revision": "sw rev"}

        response = self.client.post(reverse('post_results-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_post_results_invalid_token_SE02(self):
        ''' Requirement SE-02: Test that unauthorized client cannot access endpoint'''
        data = {
            "fw_update_started": str(self.exp_time),
            "device": "NewDevice",
            "fw_update_success": "false",
            "firmware": "2.1.0",
            "device_firmware": "1.1.0",
            "reason": "Could not update for some reason",
            "manufacturer_name": "man name",
            "model_number": "mod numb",
            "hardware_revision": self.hw_rev,
            "software_revision": "sw rev"}

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + 'badToken')
        response = self.client.post(reverse('post_results-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_post_results_invalid_request(self):
        data = {"some_invalid_data": "blablabla"}

        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.post(reverse('post_results-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "You need to provide all attributes!")

        # Test with all attributes except model_number
        data = {
            "fw_update_started": str(self.exp_time),
            "device": "NewDevice",
            "fw_update_success": "false",
            "firmware": "2.1.0",
            "device_firmware": "1.1.0",
            "reason": "Could not update for some reason",
            "manufacturer_name": "man name",
            "hardware_revision": self.hw_rev,
            "software_revision": "sw rev"}

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.post(reverse('post_results-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "You need to provide all attributes!")

    def test_post_results_fota_fail_fw_null(self):
        # Verify device starting data
        self.assertIsNone(self.dv.last_update)
        self.assertEqual(self.dv.firmware, self.fw1)
        self.assertEqual(self.dv.manufacturer_name, "ManufacturerName")
        self.assertEqual(self.dv.model_number, "ModelNumber")
        self.assertEqual(self.dv.hardware_revision, "HWRev")
        self.assertEqual(self.dv.software_revision, "SWRev")

        data = {
            "fw_update_started": str(self.exp_time),
            "device": "12345",
            "fw_update_success": "false",
            "firmware": None,
            "device_firmware": "1.1.0",
            "reason": "Could not update for some reason",
            "manufacturer_name": "man name",
            "model_number": "mod numb",
            "hardware_revision": self.hw_rev,
            "software_revision": "sw rev"}

        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.post(reverse('post_results-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Should still only be one object in db
        devices = Device.objects.all()
        self.assertEqual(1, len(devices))
        # Refresh device obj, should not have been updated
        self.dv.refresh_from_db()
        # Verify that device was not updated
        self.assertIsNone(self.dv.last_update)
        self.assertEqual(self.dv.firmware, self.fw1)
        self.assertEqual(self.dv.manufacturer_name, "ManufacturerName")
        self.assertEqual(self.dv.model_number, "ModelNumber")
        self.assertEqual(self.dv.hardware_revision, "HWRev")
        self.assertEqual(self.dv.software_revision, "SWRev")

        # Verify that the history instance was created
        history_all = History.objects.all()
        # Should only be one instance
        self.assertEqual(1, len(history_all))
        history = history_all[0]

        self.assertEqual(history.device, self.dv)
        self.assertEqual(history.fw_update_started, self.exp_time)
        self.assertFalse(history.fw_update_success)
        self.assertIsNone(history.firmware)
        self.assertEqual(history.device_firmware, str(self.fw1))
        self.assertEqual(history.reason, "Could not update for some reason")
        self.assertEqual(history.manufacturer_name, "man name")
        self.assertEqual(history.model_number, "mod numb")
        self.assertEqual(history.hardware_revision, self.hw_rev)
        self.assertEqual(history.software_revision, "sw rev")
