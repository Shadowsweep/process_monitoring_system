import psutil
import time
from datetime import datetime

def get_processes(sample_time=1):
    # Prime CPU counters
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    time.sleep(sample_time)

    processes = []
    num_cores = psutil.cpu_count(logical=True)  # for normalization

    for proc in psutil.process_iter(['pid', 'ppid', 'name', 'memory_info']):
        try:
            cpu_usage = proc.cpu_percent(interval=None) / num_cores
            mem_usage = proc.memory_info().rss / (1024 * 1024)  # MB

            # Skip idle process
            if proc.info['pid'] == 0:
                continue

            processes.append({
                "pid": proc.info['pid'],
                "ppid": proc.info['ppid'],
                "name": proc.info['name'] or "Unknown",
                "cpu_percent": round(cpu_usage, 2),
                "memory_mb": round(mem_usage, 2)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)

if __name__ == "__main__":
    data = get_processes(sample_time=2)
    print(f"\n[+] Top CPU-consuming processes at {datetime.now()}:\n")
    for p in data[:10]:
        print(f"{p['name']:<30} PID: {p['pid']:<6} CPU: {p['cpu_percent']}%   Memory: {p['memory_mb']} MB")
