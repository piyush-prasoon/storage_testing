import os
import struct
import fcntl
import pandas as pd
import pyudev
import subprocess
import re
import logging
from datetime import datetime

# Setup logging
log_filename = "storage_process.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

df = pd.DataFrame(columns=[
    "Device", "Time", "Model", "Serial Number", "Device Type", "Partitions",
    "Sector Size", "Total Sectors", "Size (Gigabytes)", "Filesystem type", "Temperature"
])

def get_sectors(device):
    try:
        with open(device, "rb") as f:
            sector_size = struct.unpack("I", fcntl.ioctl(f, 0x1268, struct.pack("I", 0)))[0]
            total_sectors = os.lseek(f.fileno(), 0, os.SEEK_END) // sector_size
            logger.info(f"Retrieved sector info for {device}: Sector Size={sector_size}, Total Sectors={total_sectors}")
            return sector_size, total_sectors
    except Exception as e:
        logger.error(f"Error retrieving sector info for {device}: {e}")
        return None, None

def get_partitions(disk):
    context = pyudev.Context()
    partitions = [
        dev.device_node for dev in context.list_devices(subsystem="block")
        if dev.get("DEVTYPE") == "partition" and dev.find_parent("block").device_node == disk
    ]
    logger.info(f"Partitions for {disk}: {partitions}")
    return partitions

def get_device_details(device):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    global df
    
    try:
        context = pyudev.Context()
        device_path = os.path.realpath(device)
        dev = None
        
        for dev_obj in context.list_devices(subsystem="block"):
            if dev_obj.device_node == device_path:
                dev = dev_obj
                break
        
        else:
            logger.warning(f"Device {device} not found.")
            return
        
        logger.info(f"Device identified: {device}, collecting info...")
        model = dev.get("ID_MODEL", "Unknown")
        serial_number = dev.get("ID_SERIAL_SHORT", "Unknown")
        device_type = dev.get("DEVTYPE", "Unknown")
        partitions = get_partitions(device)
        partition_str = ", ".join(partitions) if partitions else "No partitions found"
        sector_size, total_sectors = get_sectors(device)
        total_size = (total_sectors * sector_size) / (1024**3) if sector_size and total_sectors else "Unknown"
        size = round(total_size, 2) if isinstance(total_size, (int, float)) else "Unknown"
        filesys = dev.get("ID_FS_TYPE", "Unknown")
        temperature = get_temp(device)

        data = {
            "Device": device, "Time": timestamp, "Model": model, "Serial Number": serial_number,
            "Device Type": device_type, "Partitions": partition_str, "Sector Size": sector_size,
            "Total Sectors": total_sectors, "Size (Gigabytes)": size, "Filesystem type": filesys,
            "Temperature": temperature
        }
        
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        df.to_excel("storage_details.xlsx", index=False)
        logger.info(f"Device details saved for {device}")
    except Exception as e:
        logger.error(f"Error fetching device details for {device}: {e}")

def get_all_devices():
    context = pyudev.Context()
    devices = [
        dev.device_node for dev in context.list_devices(subsystem="block")
        if dev.device_node.startswith("/dev/sd") or dev.device_node.startswith("/dev/nvme")
    ]
    logger.info(f"Discovered devices: {devices}")
    return devices

def get_temp(device):
    try:
        output = subprocess.check_output(["smartctl", "-A", device], universal_newlines=True)
        for line in output.split("\n"):
            if "Temperature" in line or "Temperature Sensor 1" in line:
                temp_match = re.search(r'\d+', line)
                if temp_match:
                    temperature = int(temp_match.group())
                    logger.info(f"Temperature for {device}: {temperature}")
                    return temperature
        return "Unknown"
    except Exception as e:
        logger.error(f"Error retrieving temperature for {device}: {e}")
        return "Unknown"

# Main Execution
logger.info("Starting device scan...")
devices = get_all_devices()



for _ in range(3):
    for device in devices:
        get_device_details(device)

logger.info("Device scan complete.")
