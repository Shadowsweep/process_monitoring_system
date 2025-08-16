# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Host, Process, SystemInfo
from .serializers import ProcessSerializer, SystemInfoSerializer

class HostMonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.host_name = None
        await self.send(json.dumps({"message": "WebSocket connected"}))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Expected: {"hostname": "LAPTOP-7UTNLTAQ"}
        hostname = data.get("hostname")
        if hostname:
            self.host_name = hostname
            await self.send_host_data(hostname)

    async def send_host_data(self, hostname):
        try:
            host = Host.objects.get(hostname=hostname)
            # Serialize system info
            system_info = SystemInfoSerializer(host.system_info).data
            # Serialize all processes for this host (latest timestamp)
            latest_timestamp = host.processes.order_by('-timestamp').first().timestamp
            processes = host.processes.filter(timestamp=latest_timestamp)
            processes_data = ProcessSerializer(processes, many=True).data

            payload = {
                "system_info": system_info,
                "processes": processes_data
            }
            await self.send(json.dumps(payload))
        except Host.DoesNotExist:
            await self.send(json.dumps({"error": "Host not found"}))
