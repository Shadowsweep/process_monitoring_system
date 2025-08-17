''' this script tests the API key functionality by sending a POST request to the backend endpoint with a sample payload. '''
import requests
import socket
import json
from datetime import datetime

API_KEY = "6566ad98157118e80a26f9e79041df093b7a6b15496286c6d44e921ec22e1a34"  # must match settings.py
BACKEND_ENDPOINT = "http://localhost:8000/api/agent/process-data/"

payload = {
    "hostname": socket.gethostname(),
    "timestamp": datetime.now().isoformat(),
    "system_info": {
        "os_name": "TestOS",
        "processor": "TestProcessor",
        "num_cores": 4,
        "num_threads": 8,
        "ram_total_gb": 16.0,
        "ram_used_gb": 8.0,
        "ram_available_gb": 8.0,
        "storage_total_gb": 500.0,
        "storage_used_gb": 200.0,
        "storage_free_gb": 300.0
    },
    "processes": [
        {
            "pid": 123,
            "ppid": 1,
            "name": "test_process",
            "cpu_percent": 0.5,
            "memory_mb": 12.5,
            "timestamp": datetime.now().isoformat()
        }
    ]
}

headers = {
    "Content-Type": "application/json",
    "X-API-KEY": API_KEY
}

try:
    r = requests.post(BACKEND_ENDPOINT, data=json.dumps(payload), headers=headers)
    print("Status Code:", r.status_code)
    print("Response:", r.text)
except requests.exceptions.RequestException as e:
    print("Error:", e)
