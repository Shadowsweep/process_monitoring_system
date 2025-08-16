# # consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Host
from .serializers import SystemInfoSerializer, ProcessSerializer

class HostMonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.host_name = None
        self.update_task = None   # task for periodic updates

    async def disconnect(self, close_code):
        if self.update_task:
            self.update_task.cancel()

    async def receive(self, text_data):
        """
        Receives hostname from frontend once
        and starts auto-updates.
        """
        data = json.loads(text_data)
        hostname = data.get("hostname")
        if hostname:
            self.host_name = hostname
            # Start periodic updates only once
            if not self.update_task:
                self.update_task = asyncio.create_task(self.send_updates())

    async def send_updates(self):
        """
        Push updates every 1 second
        until client disconnects.
        """
        try:
            while True:
                if self.host_name:
                    # print(f"Sending updates for {self.host_name}")
                    await self.send_host_data(self.host_name)
                await asyncio.sleep(1)  # adjust interval if needed
        except asyncio.CancelledError:
            # cleanup when task is cancelled
            pass

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

    # ============= DB Methods =============

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
