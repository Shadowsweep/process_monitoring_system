# # consumers.py
# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from .models import Host, Process, SystemInfo
# from .serializers import ProcessSerializer, SystemInfoSerializer

# class HostMonitorConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         await self.accept()
#         self.host_name = None
#         await self.send(json.dumps({"message": "WebSocket connected"}))

#     async def disconnect(self, close_code):
#         pass

#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         # Expected: {"hostname": "LAPTOP-7UTNLTAQ"}
#         hostname = data.get("hostname")
#         if hostname:
#             self.host_name = hostname
#             await self.send_host_data(hostname)

#     async def send_host_data(self, hostname):
#         try:
#             host = Host.objects.get(hostname=hostname)
#             # Serialize system info
#             system_info = SystemInfoSerializer(host.system_info).data
#             # Serialize all processes for this host (latest timestamp)
#             latest_timestamp = host.processes.order_by('-timestamp').first().timestamp
#             processes = host.processes.filter(timestamp=latest_timestamp)
#             processes_data = ProcessSerializer(processes, many=True).data

#             payload = {
#                 "system_info": system_info,
#                 "processes": processes_data
#             }
#             await self.send(json.dumps(payload))
#         except Host.DoesNotExist:
#             await self.send(json.dumps({"error": "Host not found"}))
# The script we are using is for syncronous calls one now we are trying to convert into asynchronous call 


import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from datetime import datetime
from channels.db import database_sync_to_async
from .models import Host
from .serializers import SystemInfoSerializer, ProcessSerializer

class HostMonitorConsumer(AsyncWebsocketConsumer):
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        hostname = data.get("hostname")
        if hostname:
            self.host_name = hostname
            await self.send_host_data(hostname)

    async def send_host_data(self, hostname):
        host = await self.get_host(hostname)
        if not host:
            await self.send(json.dumps({"error": "Host not found"}))
            return
        
        system_info = await self.get_system_info(host)
        processes_data = await self.get_processes(host)
        
        payload = {
            "system_info": system_info,
            "processes": processes_data
        }
        await self.send(json.dumps(payload))

    @database_sync_to_async
    def get_host(self, hostname):
        try:
            return Host.objects.get(hostname=hostname)
        except Host.DoesNotExist:
            return None

    @database_sync_to_async
    def get_system_info(self, host):
        return SystemInfoSerializer(host.system_info).data

    @database_sync_to_async
    def get_processes(self, host):
        latest_timestamp = host.processes.order_by('-timestamp').first()
        if not latest_timestamp:
            return []
        processes = host.processes.filter(timestamp=latest_timestamp.timestamp)
        return ProcessSerializer(processes, many=True).data
