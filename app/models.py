from django.db import models
from pkg_resources import packaging


class Firmware(models.Model):
    fw_version = models.CharField(max_length=100)
    hw_compability = models.CharField(max_length=100)
    date_added = models.DateTimeField()
    file_name = models.CharField(max_length=100)
    file = models.BinaryField(null=True, blank=True, editable=True)

    class Meta:
        ordering = ['-fw_version']
        unique_together = ['fw_version', 'hw_compability']

    def __str__(self):
        return self.fw_version

    def get_latest_fw_object(self, hw_rev):
        if hw_rev == None or not self._meta.model.objects.filter(hw_compability__iexact=hw_rev).exists():
            return None

        objects = self._meta.model.objects.filter(hw_compability__iexact=hw_rev)
        latest = objects[0]
        for obj in objects:
            if packaging.version.parse(obj.fw_version) > packaging.version.parse(latest.fw_version):
                latest = obj

        return latest

class Device(models.Model):
    serial_number = models.CharField(max_length=100, unique=True)
    created = models.DateTimeField()
    firmware = models.ForeignKey(Firmware, on_delete=models.SET_NULL, null=True)
    last_update = models.DateTimeField(null=True, blank=True) # Null if the device has never been updated
    manufacturer_name = models.CharField(max_length=100,null=True, blank=True)
    model_number = models.CharField(max_length=100,null=True, blank=True, verbose_name='Model#')
    hardware_revision = models.CharField(max_length=100,null=True, blank=True, verbose_name='HW rev.')
    software_revision = models.CharField(max_length=100,null=True, blank=True, verbose_name='SW rev.')

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.serial_number

class History(models.Model):
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True)
    fw_update_started = models.DateTimeField(verbose_name='Timestamp')
    fw_update_success = models.BooleanField()
    firmware = models.ForeignKey(Firmware, on_delete=models.SET_NULL, null=True, verbose_name='Flashed Firmware')
    device_firmware = models.CharField(max_length=50, null=True, blank=True)
    reason = models.CharField(max_length=500, null=True, blank=True)
    manufacturer_name = models.CharField(max_length=100,null=True, blank=True)
    model_number = models.CharField(max_length=100,null=True, blank=True, verbose_name='Model#')
    hardware_revision = models.CharField(max_length=100,null=True, blank=True, verbose_name='HW rev.')
    software_revision = models.CharField(max_length=100,null=True, blank=True, verbose_name='SW rev.')

    class Meta:
        # Force plural name to be History, otherwise admin site will just append s in the end
        verbose_name_plural = "History"
        ordering = ['-fw_update_started']

    def __str__(self):
        return self.device.serial_number
