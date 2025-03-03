import psutil  # This helps us get system info like CPU, memory, and disk details
import pandas as pd  # Used to organize data and save it in an Excel file
import uuid  # Used to generate a unique identifier for each drive
from datetime import datetime  # Used for timestamps

# Function to log events with timestamps
def log_event(message):
    """Prints a message with a timestamp."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# Mapping different file system types to a more readable partition type
PARTITION_TYPE_MAP = {
    "vfat": "EFI System",
    "ext4": "Linux Filesystem",
    "ntfs": "Windows NTFS",
    "xfs": "Linux XFS",
    "btrfs": "Linux Btrfs",
    "swap": "Linux Swap",
    "exfat": "Extended FAT",
}

# Function to get temperature data for storage devices
def get_drive_temperature(device):
    """Fetch the temperature of a given device if available."""
    try:
        temps = psutil.sensors_temperatures()
        nvme_temps = []

        for sensor, entries in temps.items():
            for entry in entries:
                if "nvme" in sensor.lower():
                    nvme_temps.append(entry.current)
                if device in entry.label.lower():
                    return entry.current  # Return the first matching temperature

        if nvme_temps:
            return max(nvme_temps)
    except AttributeError:
        pass  

    return "N/A"

# Function to get details of all the drives/partitions in the system
def get_drive_metadata():
    log_event("Fetching drive metadata...")
    drives = []  

    for partition in psutil.disk_partitions(all=True): 
        device  = partition.device 

        if "/dev/sda" in device or "/dev/nvme" in device: 
            try:
                usage = psutil.disk_usage(partition.mountpoint)  
                drive_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, partition.device))  
                partition_type = PARTITION_TYPE_MAP.get(partition.fstype, "Unknown")  
                temperature = get_drive_temperature(device)
             
                drives.append({
                    "Device": partition.device,
                    "Mount Point": partition.mountpoint,
                    "File System": partition.fstype,
                    "Partition Type": partition_type,
                    "Total Size (GB)": round(usage.total / (1024**3), 2),
                    "Used Space (GB)": round(usage.used / (1024**3), 2),
                    "Free Space (GB)": round(usage.free / (1024**3), 2),
                    "Usage (%)": f"{usage.percent}%",
                    "Temperature (°C)": temperature,
                    "UUID": drive_uuid
                })

                log_event(f"Fetched data for {partition.device} ({partition.mountpoint})")
            except PermissionError:
                log_event(f"Skipping {partition.device} due to permission error.")
                continue  

    log_event("Finished fetching drive metadata.")
    return drives  

# Function to save the gathered data into an Excel file
def save_to_excel(data, filename="details.xlsx"):
    log_event(f"Saving data to {filename}...")
    df = pd.DataFrame(data)  
    df.to_excel(filename, index=False)  
    log_event(f"Drive metadata successfully saved to {filename}")

# Main execution of the script
if __name__ == "__main__":
    log_event("Script started.")
    drive_data = get_drive_metadata()  
    save_to_excel(drive_data)  
    log_event("Script completed successfully.")
