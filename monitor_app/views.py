from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import Host, Process, SystemInfo
from .serializers import HostDataSerializer, ProcessSerializer, SystemInfoSerializer
from .permissions import AgentAPIKeyPermission
from django.db.models import Max
from django.views.generic import TemplateView
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse
from django.shortcuts import render


class ProcessDataAgentView(APIView):
    """
    API endpoint for agents to send process + system data.
    Requires X-API-KEY header for authentication.
    """
    permission_classes = [AgentAPIKeyPermission]

    def post(self, request, *args, **kwargs):
        serializer = HostDataSerializer(data=request.data)
        if serializer.is_valid():
            hostname = serializer.validated_data['hostname']
            processes_data = serializer.validated_data['processes']
            system_info_data = serializer.validated_data['system_info']
            api_key = request.headers.get('X-API-KEY')

            # Validate API key against hostname
            if settings.API_KEYS.get(api_key) != hostname:
                return Response({"detail": "API key does not match hostname."}, status=status.HTTP_403_FORBIDDEN)

            with transaction.atomic():
                # Create or update host
                host, created = Host.objects.get_or_create(hostname=hostname)
                host.last_seen = timezone.now()
                host.save()

                # Save or update system info
                SystemInfo.objects.update_or_create(
                    host=host,
                    defaults=system_info_data
                )

                # Replace old processes with new snapshot
                Process.objects.filter(host=host).delete()
                process_objects = [
                    Process(
                        host=host,
                        timestamp=serializer.validated_data['timestamp'],
                        pid=proc['pid'],
                        ppid=proc['ppid'],
                        name=proc['name'],
                        cpu_percent=proc['cpu_percent'],
                        memory_mb=proc['memory_mb']
                    )
                    for proc in processes_data
                ]
                Process.objects.bulk_create(process_objects)

            return Response({"message": "Data received successfully."}, status=status.HTTP_201_CREATED)
        print("Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class LatestDataFrontendView(APIView):
#     """
#     API endpoint to get latest processes + system info for a given host.
#     """
#     def get(self, request, hostname, *args, **kwargs):
#         try:
#             host = Host.objects.get(hostname=hostname)
#             system_info = SystemInfo.objects.get(host=host)
#         except (Host.DoesNotExist, SystemInfo.DoesNotExist):
#             return Response({"detail": "Host or system info not found."}, status=status.HTTP_404_NOT_FOUND)

#         processes = Process.objects.filter(host=host).order_by('pid')
#         processes_serializer = ProcessSerializer(processes, many=True)
#         system_info_serializer = SystemInfoSerializer(system_info)

#         return Response({
#             "hostname": host.hostname,
#             "last_seen": host.last_seen,
#             "system_info": system_info_serializer.data,
#             "processes": processes_serializer.data
#         }, status=status.HTTP_200_OK)

class LatestProcessDataFrontendView(APIView):
    """
    Returns the latest process data for a given host.
    """
    def get(self, request, hostname):
        # Get latest timestamp for this host
        latest_timestamp = Process.objects.filter(
            host__hostname=hostname
        ).aggregate(latest=Max('timestamp'))['latest']

        if not latest_timestamp:
            return Response({"error": "No process data found for this host."}, status=404)

        # Get all processes for that timestamp
        processes = Process.objects.filter(
            host__hostname=hostname,
            timestamp=latest_timestamp
        )

        result = [
            {
                "pid": p.pid,
                "ppid": p.ppid,
                "name": p.name,
                "cpu_percent": p.cpu_percent,
                "memory_mb": p.memory_mb,
                "timestamp": p.timestamp
            }
            for p in processes
        ]

        return Response(result)

class ListHostsView(APIView):
    """
    API endpoint to list all known hosts with last seen timestamps.
    """
    def get(self, request, *args, **kwargs):
        hosts = Host.objects.all().order_by('hostname')
        data = [{"hostname": h.hostname, "last_seen": h.last_seen} for h in hosts]
        return Response(data, status=status.HTTP_200_OK)

# Add this view to your views.py file

class SystemInfoFrontendView(APIView):
    """
    API endpoint to get system info for a given host.
    """
    def get(self, request, hostname, *args, **kwargs):
        try:
            host = Host.objects.get(hostname=hostname)
            system_info = SystemInfo.objects.get(host=host)
        except (Host.DoesNotExist, SystemInfo.DoesNotExist):
            return Response({"detail": "Host or system info not found."}, status=status.HTTP_404_NOT_FOUND)

        system_info_serializer = SystemInfoSerializer(system_info)
        return Response(system_info_serializer.data, status=status.HTTP_200_OK)

# This Function is for aceessing the frontend
class ProcessMonitorView(TemplateView):
    """
    Render the process monitor frontend page
    """
    template_name = 'monitor_app/process_monitor.html'
    

def process_data_view(request):
    # assume JSON with hostname, timestamp, processes
    data = json.loads(request.body)

    # Save to DB if needed ...

    # Send to WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "process_group",  # broadcast group
        {
            "type": "send_process_data",
            "data": data
        }
    )

    return JsonResponse({"status": "success"})

def sockets_test(request):
    return render(request, "sockets_test.html")

def host_monitor_view(request):
    return render(request, "host_monitor.html")