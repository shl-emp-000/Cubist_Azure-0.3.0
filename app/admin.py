from django.utils import timezone
from django.contrib import admin
from .models import Device, Firmware, History
from .forms import FirmwareFormAdmin

# Register your models here.

class DeviceAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'created', 'firmware', 'last_update',  'manufacturer_name', 'model_number', 'hardware_revision', 'software_revision')
    list_filter = ('firmware', 'created', 'last_update')
    search_fields = ['serial_number']

    def get_form(self, request, obj=None, **kwargs):
        form = super(DeviceAdmin, self).get_form(request, obj, **kwargs)
        # Edit label for Firmware in the form, display both FW and HW version in the dropdown choise field.
        form.base_fields['firmware'].label_from_instance = lambda obj: "FW: {}, HW: {}".format(obj.fw_version, obj.hw_compability)
        return form

    def save_model(self, request, obj, form, change):
        if form.is_valid():
            # Take hardware_revision from firmware if it was not filled in when adding the device
            if not form.cleaned_data["hardware_revision"]:
                fw = form.cleaned_data["firmware"]
                obj.hardware_revision = fw.hw_compability

            super().save_model(request, obj, form, change)

admin.site.register(Device, DeviceAdmin)

class FirmwareAdmin(admin.ModelAdmin):
    list_display = ('fw_version', 'hw_compability', 'date_added', 'file_name', )
    list_filter = ('fw_version', 'hw_compability', 'date_added')
    search_fields = ['fw_version']
    form = FirmwareFormAdmin

    def save_model(self, request, obj, form, change):
        if form.is_valid():
            obj.fw_version = form.cleaned_data["fw_version"]
            obj.hw_compability = form.cleaned_data["hw_compability"]
            obj.date_added = timezone.now()
            if change:
                if request.FILES.get('file', False):
                    obj.file_name = request.FILES['file'].name
                    uploaded_file = request.FILES['file'].read()
                    obj.file = uploaded_file
                else:
                    # Do nothing, don't want fw image to be mandatory when editing instance
                    pass
            else:
                file_name = request.FILES['file'].name
                uploaded_file = request.FILES['file'].read()
                obj.file_name = file_name
                obj.file = uploaded_file

            super().save_model(request, obj, form, change)

admin.site.register(Firmware, FirmwareAdmin)

class HistoryAdmin(admin.ModelAdmin):
    list_display = ('fw_update_started', 'device', 'device_firmware', 'firmware', 'fw_update_success', 'reason')
    list_filter = ('fw_update_success', 'device', 'firmware', 'device_firmware')
    search_fields = ['device']

admin.site.register(History, HistoryAdmin)
