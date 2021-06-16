from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.http import HttpResponse, request
from app.models import Device, Firmware, History
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication
from api.serializers import FirmwareSerializer, FirmwareVersionSerializer, HistorySerializer
import os.path


class LatestFirmwareViewSet(viewsets.ModelViewSet):
    """
    API endpoint that only reads the latest firmware version.
    """
    queryset = Firmware.objects.all()
    http_method_names = ['get']
    serializer_class = FirmwareVersionSerializer

    def get_hw_rev_from_token(self, request):
        try:
            header = JWTTokenUserAuthentication.get_header(self, request)
            raw_token = JWTTokenUserAuthentication.get_raw_token(self, header)
            jwt_token = JWTTokenUserAuthentication.get_validated_token(self, raw_token)
            hw_rev = jwt_token.get("hw_rev")
            if hw_rev:
                return hw_rev
            else:
                return None
        except:
            return None

    def list(self, request, *args, **kwargs):
        latest_fw = Firmware.get_latest_fw_object(Firmware, self.get_hw_rev_from_token(request))
        if latest_fw is None:
            return Response(status=status.HTTP_204_NO_CONTENT)

        response = Response(FirmwareVersionSerializer(instance=latest_fw).data)
        return response


class DownloadLatestFirmwareViewSet(viewsets.ModelViewSet):
    """
    API endpoint that dowloads latest firmware.
    """
    queryset = Firmware.objects.all()
    http_method_names = ['get']
    serializer_class = FirmwareSerializer

    def get_hw_rev_from_token(self, request):
        try:
            header = JWTTokenUserAuthentication.get_header(self, request)
            raw_token = JWTTokenUserAuthentication.get_raw_token(self, header)
            jwt_token = JWTTokenUserAuthentication.get_validated_token(self, raw_token)
            hw_rev = jwt_token.get("hw_rev")
            if hw_rev:
                return hw_rev
            else:
                return None
        except:
            return None

    def list(self, request, *args, **kwargs):
        latest_fw = Firmware.get_latest_fw_object(Firmware, self.get_hw_rev_from_token(request))
        if latest_fw is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        file_extension = os.path.splitext(latest_fw.file_name)[-1]
        file_name = latest_fw.fw_version + file_extension
        contents = latest_fw.file
        response = HttpResponse(contents)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment; filename={}'.format(file_name)

        return response

class PostResultsViewSet(viewsets.ModelViewSet):
    """
    API endpoint to create a new history instance.
    """
    queryset = History.objects.all()
    http_method_names = ['post']
    serializer_class = HistorySerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)

        if not {"device", "device_firmware", "manufacturer_name", "model_number", "hardware_revision", "software_revision"} <= serializer.initial_data.keys():
            # The request does not contain the expected data
            return Response(data="You need to provide all attributes!", status=status.HTTP_400_BAD_REQUEST)

        # Make sure device exists in DB, if not create it
        try:
            device = Device.objects.get(serial_number=serializer.initial_data["device"])
        except ObjectDoesNotExist:
            # Try to get device FW
            try:
                # FW version and HW revision are unique together, will return one or None firmwares
                device_firmware = Firmware.objects.get(fw_version=serializer.initial_data["device_firmware"], hw_compability=serializer.initial_data["hardware_revision"])
            except:
                # Device running some unknow FW
                device_firmware = None
            device = Device.objects.create(serial_number=serializer.initial_data["device"], created=timezone.now(), firmware=device_firmware, last_update=None, manufacturer_name=serializer.initial_data["manufacturer_name"],
            model_number=serializer.initial_data["model_number"], hardware_revision=serializer.initial_data["hardware_revision"], software_revision=serializer.initial_data["software_revision"])
        serializer.initial_data["device"] = device.id

        # Get firmware
        try:
            # FW version and HW revision are unique together, will return one or None firmwares
            firmware = Firmware.objects.get(fw_version=serializer.initial_data["firmware"], hw_compability=serializer.initial_data["hardware_revision"])
            serializer.initial_data["firmware"] = firmware.id
        except:
            # No such firmware
            serializer.initial_data["firmware"] = None
        

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
