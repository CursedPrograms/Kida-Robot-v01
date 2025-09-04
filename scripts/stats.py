# stats.py
import psutil, socket, threading

stats_lock = threading.Lock()
system_stats = {
    "cpu": 0.0,
    "ram": 0.0,
    "temp": "N/A",
    "ip": "127.0.0.1"
}

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_milli = int(f.read())
        return f"{temp_milli / 1000:.1f}°C"
    except:
        return "N/A"

def get_system_stats():
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    return cpu, ram

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def update_stats():
    with stats_lock:
        system_stats["cpu"], system_stats["ram"] = get_system_stats()
        system_stats["temp"] = get_cpu_temp()
        system_stats["ip"] = get_local_ip()
