from django.test import TestCase
from datetime import timedelta
from django.utils import timezone
from .models import Firmware, Device, History
from django.core.exceptions import MultipleObjectsReturned

class FirmwareTestCase(TestCase):
    def setUp(self):
        now = timezone.now()

        # Add some Firmware instances to db
        Firmware.objects.create(fw_version="0.1.0", hw_compability="v3", date_added=(now - timedelta(days=10)), file_name="fw_file_v0.1.0.cyacd2", file=bytes("file_0.1.0_data",'utf-8'))
        Firmware.objects.create(fw_version="1.0.0", hw_compability="v4", date_added=(now - timedelta(days=8)), file_name="fw_file_v1.0.0.cyacd2", file=bytes("file_1.0.0_data",'utf-8'))
        Firmware.objects.create(fw_version="2.0.0", hw_compability="v5", date_added=(now - timedelta(days=6)), file_name="fw_file_v2.0.0.cyacd2", file=bytes("file_2.0.0_data",'utf-8'))

    def test_str_is_equal_to_fw_version(self):
        fw_0_1_1 = Firmware.objects.get(fw_version="0.1.0")
        fw_1_0_0 = Firmware.objects.get(fw_version="1.0.0")
        fw_2_0_0 = Firmware.objects.get(fw_version="2.0.0")

        self.assertEqual(str(fw_0_1_1), fw_0_1_1.fw_version)
        self.assertEqual(str(fw_1_0_0), fw_1_0_0.fw_version)
        self.assertEqual(str(fw_2_0_0), fw_2_0_0.fw_version)

    def test_get_latest_fw_object(self):
        expected_object = Firmware.objects.get(fw_version="0.1.0")
        test_objectet = Firmware.get_latest_fw_object(Firmware, "v3")
        self.assertEqual(expected_object, test_objectet)

        expected_object = Firmware.objects.get(fw_version="1.0.0")
        test_objectet = Firmware.get_latest_fw_object(Firmware, "v4")
        self.assertEqual(expected_object, test_objectet)

        expected_object = Firmware.objects.get(fw_version="2.0.0")
        test_objectet = Firmware.get_latest_fw_object(Firmware, "v5")
        self.assertEqual(expected_object, test_objectet)

    def test_newly_added_fw_returned(self):
        new_fw = Firmware.objects.create(fw_version="3.0.0", hw_compability="v5", date_added=timezone.now(), file_name="fw_file_v3.0.0.cyacd2", file=bytes("file_3.0.0_data",'utf-8'))
        new_fw.save()
        test_objectet = Firmware.get_latest_fw_object(Firmware, "v5")
        self.assertEqual(new_fw, test_objectet)

        # No new fw for other hardware revisions
        expected_object = Firmware.objects.get(fw_version="0.1.0")
        test_objectet = Firmware.get_latest_fw_object(Firmware, "v3")
        self.assertEqual(expected_object, test_objectet)

        expected_object = Firmware.objects.get(fw_version="1.0.0")
        test_objectet = Firmware.get_latest_fw_object(Firmware, "v4")
        self.assertEqual(expected_object, test_objectet)


class DeviceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()

        # Add some Firmware and Device instances to db
        fw1 = Firmware.objects.create(fw_version="0.1.0", hw_compability="v5", date_added=(now - timedelta(days=10)), file_name="fw_file_v0.1.0.cyacd2", file=bytes("file_0.1.0_data",'utf-8'))
        fw2 = Firmware.objects.create(fw_version="1.0.0", hw_compability="v5", date_added=(now - timedelta(days=8)), file_name="fw_file_v1.0.0.cyacd2", file=bytes("file_1.0.0_data",'utf-8'))
        fw3 = Firmware.objects.create(fw_version="2.0.0", hw_compability="v5", date_added=(now - timedelta(days=6)), file_name="fw_file_v2.0.0.cyacd2", file=bytes("file_2.0.0_data",'utf-8'))

        Device.objects.create(serial_number="12345", created=(now - timedelta(days=9)), firmware=fw1)
        Device.objects.create(serial_number="54321", created=(now - timedelta(days=8)), firmware=fw2, last_update=(now - timedelta(days=7)))
        Device.objects.create(serial_number="56789", created=(now - timedelta(days=7)), firmware=fw3, last_update=(now - timedelta(days=5)),
        manufacturer_name="ManufacturerName", model_number="ModelNumber", hardware_revision="HWRev", software_revision="SWRev")

    def test_str_is_equal_to_serial_number(self):
        device1 = Device.objects.get(serial_number="12345")
        device2 = Device.objects.get(serial_number="54321")
        device3 = Device.objects.get(serial_number="56789")

        self.assertEqual(str(device1), device1.serial_number)
        self.assertEqual(str(device2), device2.serial_number)
        self.assertEqual(str(device3), device3.serial_number)
        

class HistoryTestCase(TestCase):
    def setUp(self):
        now = timezone.now()

        self.fw = Firmware.objects.create(fw_version="0.1.0", hw_compability="v5", date_added=(now - timedelta(days=10)), file_name="fw_file_v0.1.0.cyacd2", file=bytes("file_0.1.0_data",'utf-8'))
        self.dv = Device.objects.create(serial_number="12345", created=(now - timedelta(days=9)), firmware=self.fw)
        History.objects.create(device=self.dv, fw_update_started=now, fw_update_success=False, firmware=self.fw, device_firmware="", reason="Failed to update")

    def test_str_is_equal_to_serial_number(self):
        history = History.objects.get(device=self.dv.id)

        self.assertEqual(str(history), history.device.serial_number)

    def test_list_of_history_objects_returned(self):
        history = History.objects.get(device=self.dv.id)
        self.assertFalse(type(history) == list)

        # Add one more history instance and we should get a list back
        History.objects.create(device=Device.objects.get(id=self.dv.id), fw_update_started=timezone.now(), fw_update_success=True, firmware=Firmware.objects.get(id=self.fw.id), device_firmware="", reason="Success")
        self.assertRaises(MultipleObjectsReturned, History.objects.get, device=self.dv.id)

        histories = History.objects.filter(device=self.dv.id)
        self.assertEqual(2, len(histories))
        self.assertTrue(histories[0].fw_update_success == True) # Sorted by latest timestamp first
        self.assertTrue(histories[1].fw_update_success == False)
