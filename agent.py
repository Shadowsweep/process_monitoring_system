# Implementing script so that we can also get real time CPU usage by adding time sleep so that 1 sec measument can be done 
import psutil
import requests
import time
import json
import socket
import platform
import shutil
from datetime import datetime

# =======================
# CONFIGURATION
# =======================
BACKEND_ENDPOINT = "http://localhost:8000/api/agent/process-data/"
AGENT_API_KEY = "6566ad98157118e80a26f9e79041df093b7a6b15496286c6d44e921ec22e1a34"
COLLECTION_INTERVAL_SECONDS = 5

# =======================
# DATA COLLECTION
# =======================
def get_system_info():
    """Collects system information in the exact format the serializer expects."""
    vm = psutil.virtual_memory()
    total, used, free = shutil.disk_usage("/")
    return {
        "os_name": platform.system(),
        "processor": platform.processor(),
        "num_cores": psutil.cpu_count(logical=False),
        "num_threads": psutil.cpu_count(logical=True),
        "ram_total_gb": round(vm.total / (1024 ** 3), 2),
        "ram_used_gb": round(vm.used / (1024 ** 3), 2),
        "ram_available_gb": round(vm.available / (1024 ** 3), 2),
        "storage_total_gb": round(total / (1024 ** 3), 2),
        "storage_used_gb": round(used / (1024 ** 3), 2),
        "storage_free_gb": round(free / (1024 ** 3), 2)
    }

def get_process_info():
    """Collects running processes with ACCURATE CPU usage measurements."""
    processes_info = []
    timestamp_now = datetime.now().isoformat()
    
    # STEP 1: Initialize CPU measurement for all processes
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Initializing CPU measurements...")
    process_objects = []
    
    for proc in psutil.process_iter(['pid', 'name', 'ppid']):
        try:
            # Initialize CPU measurement (this call returns 0.0 but is necessary)
            proc.cpu_percent()
            process_objects.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    # STEP 2: Wait for measurement interval
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Measuring CPU usage over 1 second...")
    time.sleep(1.0)  # Critical: This allows CPU usage to be calculated
    
    # STEP 3: Collect actual CPU data
    for proc in process_objects:
        try:
            # Now cpu_percent() returns actual usage
            cpu_usage = proc.cpu_percent()
            
            # Get process info
            pinfo = proc.as_dict(attrs=['pid', 'name', 'ppid'])
            pinfo['name'] = pinfo.get('name') or f"PID-{proc.pid}"
            pinfo['memory_mb'] = round(proc.memory_info().rss / (1024 * 1024), 2)
            pinfo['cpu_percent'] = round(cpu_usage, 2)
            pinfo['timestamp'] = timestamp_now
            processes_info.append(pinfo)
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] CPU measurement complete.")
    return processes_info

def get_hostname():
    """Returns the machine hostname."""
    return socket.gethostname()

def send_data_to_backend(payload):
    """Sends data to Django backend with better error handling."""
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": AGENT_API_KEY
    }
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sending data to backend...")
        response = requests.post(BACKEND_ENDPOINT, data=json.dumps(payload), headers=headers, timeout=10)
        response.raise_for_status()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ Data sent successfully. Status: {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Server not reachable at {BACKEND_ENDPOINT}")
        
    except requests.exceptions.Timeout:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Request timed out after 10 seconds")
        
    except requests.exceptions.HTTPError as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ HTTP Error {response.status_code}")
        try:
            error_detail = response.json()
            print(f"Backend error: {json.dumps(error_detail, indent=2)}")
        except:
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Request failed: {e}")

# =======================
# MAIN LOOP
# =======================
def main():
    hostname = get_hostname()
    print("=" * 60)
    print(f"System Monitor Agent Started")
    print(f"Host: {hostname}")
    print(f"Backend: {BACKEND_ENDPOINT}")
    print(f"Interval: {COLLECTION_INTERVAL_SECONDS} seconds")
    print("=" * 60)
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            start_time = time.time()
            
            print(f"\n--- Cycle {cycle_count} Started ---")
            
            # Collect all data
            system_info = get_system_info()
            processes = get_process_info()
            
            payload = {
                "hostname": hostname,
                "timestamp": datetime.now().isoformat(),
                "system_info": system_info,
                "processes": processes
            }
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Collected {len(processes)} processes")
            
            # Show top CPU processes for debugging
            top_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]
            if top_cpu:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Top CPU processes:")
                for proc in top_cpu:
                    print(f"  - {proc['name']}: {proc['cpu_percent']}% CPU, {proc['memory_mb']} MB")
            
            # Send to backend
            send_data_to_backend(payload)
            
            # Calculate timing
            elapsed_time = time.time() - start_time
            sleep_time = max(0, COLLECTION_INTERVAL_SECONDS - elapsed_time)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Cycle {cycle_count} completed in {elapsed_time:.2f}s")
            
            if sleep_time > 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting {sleep_time:.1f}s until next cycle...")
                time.sleep(sleep_time)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Cycle took longer than interval!")
                
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Agent stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Agent crashed: {e}")
        raise

if __name__ == "__main__":
    main()