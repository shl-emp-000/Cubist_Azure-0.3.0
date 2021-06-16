from app.models import Firmware, History, Device
from rest_framework import serializers
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class FirmwareSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Firmware
        fields = ['fw_version', 'file_name', 'file']

class FirmwareVersionSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Firmware
        fields = ['fw_version']

class HistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = History
        fields = ['device', 'fw_update_started', 'fw_update_success', 'firmware', 'device_firmware', 'reason', 'manufacturer_name',
        'model_number', 'hardware_revision', 'software_revision']

    def create(self, validated_data):
        instance = History.objects.create(**validated_data)
        if instance.fw_update_success:
            try:
                Device.objects.filter(serial_number=instance.device.serial_number).update(
                    firmware=instance.firmware, last_update=instance.fw_update_started, manufacturer_name=instance.manufacturer_name,
                    model_number=instance.model_number, hardware_revision=instance.hardware_revision, software_revision=instance.software_revision)
            except:
                logger.warning("Device with serial number {} does not exist! Creating device in Views must have failed.".format(instance.device.serial_number))

        return instance

