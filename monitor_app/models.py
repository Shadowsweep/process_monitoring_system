from django.db import models
from django.utils import timezone

class Host(models.Model):
    hostname = models.CharField(max_length=255, unique=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.hostname

class Process(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name='processes')
    timestamp = models.DateTimeField()
    pid = models.IntegerField()
    ppid = models.IntegerField()
    name = models.CharField(max_length=255)
    cpu_percent = models.FloatField()
    memory_mb = models.FloatField()

    class Meta:
        ordering = ['-timestamp', 'pid']
        unique_together = ('host', 'timestamp', 'pid')

    def __str__(self):
        return f"{self.name} (PID: {self.pid}) on {self.host.hostname}"

class SystemInfo(models.Model):
    host = models.OneToOneField(Host, on_delete=models.CASCADE, related_name='system_info')
    timestamp = models.DateTimeField(auto_now=True)
    os_name = models.CharField(max_length=255)
    processor = models.CharField(max_length=255)
    num_cores = models.IntegerField()
    num_threads = models.IntegerField()
    ram_total_gb = models.FloatField()
    ram_used_gb = models.FloatField()
    ram_available_gb = models.FloatField()
    storage_total_gb = models.FloatField()
    storage_used_gb = models.FloatField()
    storage_free_gb = models.FloatField()

    def __str__(self):
        return f"System Info for {self.host.hostname}"