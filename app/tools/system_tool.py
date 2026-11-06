import psutil
import os
from pathlib import Path


def get_system_metrics():
    """
    Collect actual system resource metrics using psutil.
    """

    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)

    # RAM usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent

    # Disk usage
    drive = Path.cwd().anchor
    disk = psutil.disk_usage(drive)
    disk_percent = disk.percent

    # Determine overall health
    health = "HEALTHY"

    if (
        cpu_percent >= 90
        or memory_percent >= 90
        or disk_percent >= 95
    ):
        health = "CRITICAL"

    elif (
        cpu_percent >= 75
        or memory_percent >= 80
        or disk_percent >= 85
    ):
        health = "WARNING"

    return {
        "platform": os.name,
        "cpu_percent": round(cpu_percent, 2),
        "memory_percent": round(memory_percent, 2),
        "memory_used_gb": round(memory.used / (1024 ** 3), 2),
        "memory_total_gb": round(memory.total / (1024 ** 3), 2),
        "disk_percent": round(disk_percent, 2),
        "disk_used_gb": round(disk.used / (1024 ** 3), 2),
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
        "health": health,
        "message": f"System health is {health}."
    }


def check_service_status(service_name):
    """
    Existing simulated service monitoring.
    These are not real external service checks.
    """

    services = {
        "vpn": "OPERATIONAL",
        "email": "OPERATIONAL",
        "database": "OPERATIONAL",
        "firewall": "OPERATIONAL",
        "web": "OPERATIONAL"
    }

    service = service_name.lower().strip()

    if service not in services:
        return {
            "service": service_name,
            "status": "UNKNOWN",
            "message": "Service is not registered in the monitoring system."
        }

    return {
        "service": service,
        "status": services[service],
        "message": "This is simulated monitoring data."
    }