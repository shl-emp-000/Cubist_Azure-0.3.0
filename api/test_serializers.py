from django.test import TestCase
from rest_framework import serializers
from .serializers import FirmwareSerializer, FirmwareVersionSerializer, HistorySerializer
from app.models import Device, Firmware, History
from django.utils import timezone
from datetime import timedelta, datetime
from django.utils.dateparse import parse_datetime
from io import BytesIO
import base64


class FirmwareSerializerTest(TestCase):

    def setUp(self):
        now = timezone.now()

        self.firmware_attributes = {
            'fw_version': '1.0.0',
            'hw_compability': 'v6',
            'date_added': str(now),
            'file_name': 'fw_file_v1.0.0.cyacd2',
            'file': bytes("file_1.0.0_data: \0x00\0x01",'utf-8')
        }

        self.firmware = Firmware.objects.create(**self.firmware_attributes)
        self.serializer = FirmwareSerializer(instance=self.firmware)

    def test_contains_expected_fields(self):
        data = self.serializer.data

        self.assertEqual(set(data.keys()), set(['fw_version', 'file_name', 'file']))

    def test_field_content(self):
        data = self.serializer.data

        self.assertEqual(data['fw_version'], self.firmware_attributes['fw_version'])
        self.assertEqual(data['file_name'], self.firmware_attributes['file_name'])
        self.assertEqual(base64.b64decode(data['file']), self.firmware_attributes['file'])


class FirmwareVersionSerializerTest(TestCase):

    def setUp(self):
        now = timezone.now()

        self.firmware_attributes = {
            'fw_version': '1.0.0',
            'hw_compability': 'v6',
            'date_added': str(now),
            'file_name': 'fw_file_v1.0.0.cyacd2',
            'file': bytes("file_1.0.0_data: \0x00\0x01",'utf-8')
        }

        self.serializer_data = {
            'fw_version': '1.0.0',
            'hw_compability': 'v6',
            'date_added': str(now),
            'file_name': 'fw_file_v1.0.0.cyacd2'
        }

        self.firmware = Firmware.objects.create(**self.firmware_attributes)
        self.serializer = FirmwareVersionSerializer(instance=self.firmware)


    def test_contains_expected_fields(self):
        data = self.serializer.data

        self.assertEqual(set(data.keys()), set(['fw_version']))

    def test_field_content(self):
        data = self.serializer.data

        self.assertEqual(data['fw_version'], self.firmware_attributes['fw_version'])


class HistorySerializerTest(TestCase):

    def setUp(self):
        self.now = timezone.now()

        self.fw1 = Firmware.objects.create(fw_version="1.1.0", hw_compability="v6", date_added=(self.now - timedelta(days=10)), file_name="fw_file_v1.1.0.cyacd2", file=bytes("file_1.1.0_data",'utf-8'))
        self.fw2 = Firmware.objects.create(fw_version="2.1.0", hw_compability="v6", date_added=(self.now - timedelta(days=5)), file_name="fw_file_v2.1.0.cyacd2", file=bytes("file_2.1.0_data",'utf-8'))
        self.dv = Device.objects.create(serial_number="12345", created=(self.now - timedelta(days=7)), firmware=self.fw1, last_update=None,
        manufacturer_name="ManufacturerName", model_number="ModelNumber", hardware_revision="HWRev", software_revision="SWRev")

        self.history_attributes = {
            'device': self.dv,
            'fw_update_started': self.now,
            'fw_update_success': 'True',
            'firmware': self.fw2,
            'device_firmware': self.fw1.fw_version,
            'reason': "OK", 
            'manufacturer_name': 'ManufacturerNameNEW',
            'model_number': 'ModelNumberNEW',
            'hardware_revision': 'HWRevNEW',
            'software_revision': 'SWRevNEW'
        }

        self.serializer_data = {
            'fw_version': '1.0.0',
            'hw_compability': 'v6',
            'date_added': str(self.now),
            'file_name': 'fw_file_v1.0.0.cyacd2'
        }

        self.history = History.objects.create(**self.history_attributes)
        self.serializer = HistorySerializer(instance=self.history)


    def test_contains_expected_fields(self):
        data = self.serializer.data

        self.assertEqual(set(data.keys()), set(["device", "fw_update_success", "fw_update_started", "firmware", "device_firmware", "reason", "manufacturer_name", "model_number", "hardware_revision", "software_revision"]))

    def test_field_content(self):
        data = self.serializer.data

        self.assertEqual(data['device'], self.dv.id)
        self.assertEqual(data['fw_update_success'], bool(self.history_attributes['fw_update_success']))
        self.assertEqual(parse_datetime(data['fw_update_started']), self.now)
        self.assertEqual(data['firmware'], self.fw2.id)
        self.assertEqual(data['device_firmware'], self.fw1.fw_version)
        self.assertEqual(data['reason'], self.history_attributes['reason'])
        self.assertEqual(data['manufacturer_name'], self.history_attributes['manufacturer_name'])
        self.assertEqual(data['model_number'], self.history_attributes['model_number'])
        self.assertEqual(data['hardware_revision'], self.history_attributes['hardware_revision'])
        self.assertEqual(data['software_revision'], self.history_attributes['software_revision'])

    def test_create_fota_success(self):
        new_time = timezone.now()
        new_history_attributes = {
            'device': self.dv.id,
            'fw_update_started': new_time.isoformat(),
            'fw_update_success': 'True',
            'firmware': self.fw2.id,
            'device_firmware': self.fw1.fw_version,
            'reason': "OK", 
            'manufacturer_name': 'ManufacturerNameNEWEST',
            'model_number': 'ModelNumberNEWEST',
            'hardware_revision': 'HWRevNEWEST',
            'software_revision': 'SWRevNEWEST'
        }
        
        serializer = HistorySerializer(data=new_history_attributes)
        self.assertTrue(serializer.is_valid())

        serializer.save()
        # Refresh device obj, should have been updated
        self.dv.refresh_from_db()
        self.assertEqual(self.dv.firmware, self.fw2)
        self.assertEqual(self.dv.last_update.isoformat(), new_time.isoformat())
        self.assertEqual(self.dv.manufacturer_name, new_history_attributes['manufacturer_name'])
        self.assertEqual(self.dv.model_number, new_history_attributes['model_number'])
        self.assertEqual(self.dv.hardware_revision, new_history_attributes['hardware_revision'])
        self.assertEqual(self.dv.software_revision, new_history_attributes['software_revision'])

        # Verify that another history instance was created
        history_all = History.objects.all()
        # Should only be two instance
        self.assertEqual(2, len(history_all))
        self.assertTrue(history_all[0].fw_update_started.isoformat() > history_all[1].fw_update_started.isoformat())
        history = history_all[0]

        self.assertEqual(history.device, self.dv)
        self.assertEqual(history.fw_update_started, new_time)
        self.assertTrue(history.fw_update_success)
        self.assertEqual(history.firmware, self.fw2)
        self.assertEqual(history.device_firmware, "1.1.0")
        self.assertEqual(history.reason, "OK")
        self.assertEqual(history.manufacturer_name, new_history_attributes['manufacturer_name'])
        self.assertEqual(history.model_number, new_history_attributes['model_number'])
        self.assertEqual(history.hardware_revision, new_history_attributes['hardware_revision'])
        self.assertEqual(history.software_revision, new_history_attributes['software_revision'])

    def test_create_fota_fail(self):
        new_time = timezone.now()
        new_history_attributes = {
            'device': self.dv.id,
            'fw_update_started': new_time.isoformat(),
            'fw_update_success': 'False',
            'firmware': self.fw2.id,
            'device_firmware': self.fw1.fw_version,
            'reason': "FAIL", 
            'manufacturer_name': 'ManufacturerNameNEWEST',
            'model_number': 'ModelNumberNEWEST',
            'hardware_revision': 'HWRevNEWEST',
            'software_revision': 'SWRevNEWEST'
        }
        
        serializer = HistorySerializer(data=new_history_attributes)
        self.assertTrue(serializer.is_valid())

        serializer.save()
        # Save expected values before refresing db obj
        exp_man_name = self.dv.manufacturer_name
        exp_mod_numb = self.dv.model_number
        exp_hw_rev = self.dv.hardware_revision
        exp_sw_rev = self.dv.software_revision
        # Refresh device obj, should NOT have been updated
        self.dv.refresh_from_db()
        self.assertEqual(self.dv.firmware, self.fw1)
        self.assertIsNone(self.dv.last_update)
        self.assertEqual(self.dv.manufacturer_name, exp_man_name)
        self.assertEqual(self.dv.model_number, exp_mod_numb)
        self.assertEqual(self.dv.hardware_revision, exp_hw_rev)
        self.assertEqual(self.dv.software_revision, exp_sw_rev)

        # Verify that another history instance was created
        history_all = History.objects.all()
        # Should only be two instance
        self.assertEqual(2, len(history_all))
        self.assertTrue(history_all[0].fw_update_started.isoformat() > history_all[1].fw_update_started.isoformat())
        history = history_all[0]

        self.assertEqual(history.device, self.dv)
        self.assertEqual(history.fw_update_started, new_time)
        self.assertFalse(history.fw_update_success)
        self.assertEqual(history.firmware, self.fw2)
        self.assertEqual(history.device_firmware, "1.1.0")
        self.assertEqual(history.reason, "FAIL")
        self.assertEqual(history.manufacturer_name, new_history_attributes['manufacturer_name'])
        self.assertEqual(history.model_number, new_history_attributes['model_number'])
        self.assertEqual(history.hardware_revision, new_history_attributes['hardware_revision'])
        self.assertEqual(history.software_revision, new_history_attributes['software_revision'])
