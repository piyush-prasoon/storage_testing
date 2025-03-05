import os #used to  communicate and obtain information from the OS
import struct #this allows you to convert between Python values and C-style binary data structures. 
import fcntl # used to execute fcntl() and ioctl() system calls used for managing file descriptors, locking files, and controlling devices.
import pandas as pd #used to effciently stor data into a database and writing it into an excel sheet
import pyudev #pyudev is used to interact with hardware devices(USB,storage,etc), exclusively for linux.
import subprocess #allows us to run commands on the terminal
import re #used to find patterns in texts
import logging #used to create log files for our reference
import psutil #allows us to monitor system performance and resource usage
from datetime import datetime
import uuid #  helps us fetch the UUID of a specific device

# Initialize an empty DataFrame with relevant columns
df = pd.DataFrame(columns=["Device", "Model", "UUID","Serial Number", "Device Type", "Partitions", "Sector Size", "Total Sectors", "Size (Gigabytes)","Free space(GB)","Filesystem type","Temperature(Celsius)"])

def get_sectors(device):
    try:
        with open(device, "rb") as f:  #reading the contents of a specific device in binaries
            sector_size = struct.unpack("I", fcntl.ioctl(f, 0x1268 , struct.pack("I", 0)))[0] #0x1268 is a command used to obtain the size of the sectors
            total_sectors = os.lseek(f.fileno(), 0, os.SEEK_END) // sector_size #os.lseek and fileno() are used to ciunt all the sectors within the device  
            return sector_size, total_sectors
    except Exception as e:
        print(f"\nError retrieving sector info for {device}: {e}")
        return None, None


def get_partitions(disk):
    context = pyudev.Context() #to make use of pyudev, the context must be created which lets us query and interact to the linux device/disk manager
    partitions = [
        dev.device_node for dev in context.list_devices(subsystem="block")
        if dev.get("DEVTYPE") == "partition" and dev.find_parent("block").device_node == disk  #searches for all the sub blocks in a device having a common basename
    ] 
    return partitions


def get_device_details(device):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        """Retrieve detailed information about a storage device."""
        global df  # Ensure we modify the global DataFrame
        sysfs_path = f"/sys/class/block/{os.path.basename(device)}/size" #defining the the path if the system being assessed

        try:
            context = pyudev.Context()
            device_path = os.path.realpath(device) #obtaining the path of the the device
            dev = None
            for dev_obj in context.list_devices(subsystem="block"): #checks for all the systems in the storage 
                if dev_obj.device_node == device_path: #looks for th specific device for which we require the status of.
                    dev = dev_obj
                    logger.info(f'{device} found: collecting info------------------------------------------------------------')
                    break

            else:
                    print(f"\nDevice {device} not found.")
                    return

            # Retrieve basic device details using dev.get() function part of the pyudev module
            model = dev.get("ID_MODEL", "Unknown")
            serial_number = dev.get("ID_SERIAL_SHORT", "Unknown")
            device_type = dev.get("DEVTYPE", "Unknown")
            logger.info("device info fecthed successfully")

            # Get partitions
            partitions = get_partitions(device)
            partition_str = ",".join(partitions) if partitions else  "None" # listing the partitions in the form of a string 
            logger.info(f"partititons on {device} : {partition_str}")

            sector_size, total_sectors = get_sectors(device)
            total_size = (total_sectors * sector_size)/(1024**3) if sector_size and total_sectors else "Unknown" #calculating the total space available within the device in GB
            size = round(total_size,2) #rounding off this value to 2 decimal places
            logger.info(f"total size: {size}")
            filesys = dev.get("ID_FS_TYPE","Unknown")
            logger.info(f"filesystem: {filesys}")

            tempr=get_temp(device)
            
            mount_point = None
            for partition in psutil.disk_partitions(all=True):
                if partition.device == device:
                    mount_point = partition.mountpoint #we use this method to find free space because the disk_usage method does not work without a mount point
                    break

            if mount_point:
                free_space = round(psutil.disk_usage(mount_point).free / (1024**3),2)  # Convert to GB
                logger.info(f"free sapce recorded: {free_space}")
            else:
                free_space = "Unknown"  


            # Store details in data in the form of a dictionary
            data = {
                "Device": device,
                "UUID" : str(uuid.uuid5(uuid.NAMESPACE_DNS, device)), #fetches the UUID of the device
                "Time": timestamp,
                "Model": model,
                "Serial Number": serial_number,
                "Device Type": device_type,
                "Partitions": partition_str,
                "Sector Size": sector_size,
                "Total Sectors": total_sectors,
                "Size (Gigabytes)": size,
                "Free space(GB)": free_space,
                "Filesystem type": filesys,
                "Temperature(Celsius)" : tempr
            }
            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True) #entering the values of "data" into a dataframe
            df.to_excel("storage details.xlsx", index=False) # converting th edataframe into an excel 
            logger.info(f"data for {device} entered into excel sheet.")
            print("saved as excel")


        except Exception as e:
            logger.error(f"error fetching details for {device}:{e}")


def get_all_devices():
    context = pyudev.Context()
    devices = [
        dev.device_node for dev in context.list_devices(subsystem="block") #lists all the devices in the storage
        if dev.device_node.startswith("/dev/sd") or dev.device_node.startswith("/dev/nvme") #takes all the devices having sd or nvme in the basename
    ]
    return devices

def get_temp(device):
    try:
        output = subprocess.check_output(["smartctl", "-A", device], universal_newlines=True)
        for line in output.split("\n"):
            if "Temperature" in line or "Temperature Sensor 1" in line:
                t = re.search(r'\d+', line) # Extract last column (temperature)
                t = int(t.group())
                logger.info(f"temperature of {device} found:{t}")
                return t       
        return "Unknown"  # If no temperature found
    except Exception as e:
        logger.error(f"Error retrieving temperature for {device}: {e}")
        return f"unknown"



# Main Execution
devices = get_all_devices()
logger   = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)#creating a logger object
file_handler = logging.FileHandler('my_application.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')#setting the format of the log file 
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
for i in range(0,3):
    for device in devices:
        get_device_details(device)
        # Get current process info
        pid = os.getpid()  # Get Process ID
        process = psutil.Process(pid)

        # Get CPU and memory usage
        cpu_usage = process.cpu_percent(interval=1)
        memory_usage = process.memory_info().rss / (1024 * 1024)  # Convert to MB
        logger.info(f"system stats: cpu usage: {cpu_usage},memory usage: {memory_usage}")
logger.info("END")