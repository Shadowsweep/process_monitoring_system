from rest_framework import serializers
from .models import Host, Process ,SystemInfo

class ProcessSerializer(serializers.ModelSerializer):
    """
    Serializer for Process model. Used for both input (from agent) and output (to frontend).
    """
    class Meta:
        model = Process
        fields = ['pid', 'ppid', 'name', 'cpu_percent', 'memory_mb', 'timestamp']

class SystemInfoSerializer(serializers.ModelSerializer):
    """
    Serializer for the SystemInfo model.
    """
    class Meta:
        model = SystemInfo
        exclude = ['id', 'host', 'timestamp'] # Exclude fields not sent by agent or auto-generated

class HostDataSerializer(serializers.Serializer):
    """
    Updated serializer for receiving combined host, process, and system data.
    """
    hostname = serializers.CharField(max_length=255)
    timestamp = serializers.DateTimeField()
    processes = ProcessSerializer(many=True)
    system_info = SystemInfoSerializer()