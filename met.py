import psutil  # This helps us get system info like CPU, memory, and disk details
import pandas as pd  # Used to organize data and save it in an Excel file
import uuid  # Used to generate a unique identifier for each drive

# Mapping different file system types to a more readable partition type
PARTITION_TYPE_MAP = {
    "vfat": "EFI System",  # Used for boot partitions
    "ext4": "Linux Filesystem",  # Common in Linux systems
    "ntfs": "Windows NTFS",  # Used in Windows OS
    "xfs": "Linux XFS",  # Another Linux file system
    "btrfs": "Linux Btrfs",  # Advanced Linux file system
    "swap": "Linux Swap",  # Used for swap memory
    "exfat": "Extended FAT",  # Used for external drives (USBs, SD cards)
}

# Function to get details of all the drives/partitions in the system
def get_drive_metadata():
    """This function fetches details of all the drives connected to the system."""
    
    drives = []  # This will store details of all the drives

    # Loop through all detected partitions
    for partition in psutil.disk_partitions(all=True):  
        try:
            # Get total, used, and free space of the partition
            usage = psutil.disk_usage(partition.mountpoint)  
            
            # Generate a fake UUID (since we can't fetch real UUID without system commands)
            drive_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, partition.device))  
            
            # Find partition type from the dictionary above, otherwise label it "Unknown"
            partition_type = PARTITION_TYPE_MAP.get(partition.fstype, "Unknown")  

            # Add all drive details into a dictionary and store it in the list
            drives.append({
                "Device": partition.device,  # e.g., "/dev/sda1" or "C:\"
                "Mount Point": partition.mountpoint,  # Where it is mounted
                "File System": partition.fstype,  # e.g., "ext4", "ntfs", "fat32" filesystem types
                "Partition Type": partition_type,  # Human-readable partition type
                "Total Size (GB)": round(usage.total / (1024**3), 2),  # Convert bytes to GB
                "Used Space (GB)": round(usage.used / (1024**3), 2),  # Convert bytes to GB
                "Free Space (GB)": round(usage.free / (1024**3), 2),  # Convert bytes to GB
                "Usage (%)": f"{usage.percent}%",  # Show how much space is used in %
                "UUID": drive_uuid  # Assign a unique ID to each drive
            })
        except PermissionError:
            # Some system partitions may not be accessible, so we just skip them
            continue  

    return drives  # Return the list containing all drive information 

# Function to save the gathered data into an Excel file
def save_to_excel(data, filename="drive_details.xlsx"):
    """This function saves drive information to an Excel file."""
    
    df = pd.DataFrame(data)  # Convert the list into a Pandas DataFrame (table format)
    df.to_excel(filename, index=False)  # Save the DataFrame into an Excel file
    
    # Prints message that file is saved 
    print(f"✅ Drive metadata saved to {filename}")

# Main execution of the script
if __name__ == "__main__":
    drive_data = get_drive_metadata()  # Call the function to fetch drive metadata
    save_to_excel(drive_data)  # Save the metadata information into an Excel file
import psutil  # This helps us get system info like CPU, memory, and disk details
import pandas as pd  # Used to organize data and save it in an Excel file
import uuid  # Used to generate a unique identifier for each drive

# Mapping different file system types to a more readable partition type
PARTITION_TYPE_MAP = {
    "vfat": "EFI System",  # Used for boot partitions
    "ext4": "Linux Filesystem",  # Common in Linux systems
    "ntfs": "Windows NTFS",  # Used in Windows OS
    "xfs": "Linux XFS",  # Another Linux file system
    "btrfs": "Linux Btrfs",  # Advanced Linux file system
    "swap": "Linux Swap",  # Used for swap memory
    "exfat": "Extended FAT",  # Used for external drives (USBs, SD cards)
}

# Function to get details of all the drives/partitions in the system
def get_drive_metadata():
    """This function fetches details of all the drives connected to the system."""
    
    drives = []  # This will store details of all the drives

    # Loop through all detected partitions
    for partition in psutil.disk_partitions(all=True):  
        try:
            # Get total, used, and free space of the partition
            usage = psutil.disk_usage(partition.mountpoint)  
            
            # Generate a fake UUID (since we can't fetch real UUID without system commands)
            drive_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, partition.device))  
            
            # Find partition type from the dictionary above, otherwise label it "Unknown"
            partition_type = PARTITION_TYPE_MAP.get(partition.fstype, "Unknown")  

            # Add all drive details into a dictionary and store it in the list
            drives.append({
                "Device": partition.device,  # e.g., "/dev/sda1" or "C:\"
                "Mount Point": partition.mountpoint,  # Where it is mounted
                "File System": partition.fstype,  # e.g., "ext4", "ntfs", "fat32" filesystem types
                "Partition Type": partition_type,  # Human-readable partition type
                "Total Size (GB)": round(usage.total / (1024**3), 2),  # Convert bytes to GB
                "Used Space (GB)": round(usage.used / (1024**3), 2),  # Convert bytes to GB
                "Free Space (GB)": round(usage.free / (1024**3), 2),  # Convert bytes to GB
                "Usage (%)": f"{usage.percent}%",  # Show how much space is used in %
                "UUID": drive_uuid  # Assign a unique ID to each drive
            })
        except PermissionError:
            # Some system partitions may not be accessible, so we just skip them
            continue  

    return drives  # Return the list containing all drive information 

# Function to save the gathered data into an Excel file
def save_to_excel(data, filename="drive_details.xlsx"):
    """This function saves drive information to an Excel file."""
    
    df = pd.DataFrame(data)  # Convert the list into a Pandas DataFrame (table format)
    df.to_excel(filename, index=False)  # Save the DataFrame into an Excel file
    
    # Prints message that file is saved 
    print(f"Drive metadata saved to {filename}")

# Main execution of the script
if __name__ == "__main__":
    drive_data = get_drive_metadata()  # Call the function to fetch drive metadata
    save_to_excel(drive_data)  # Save the metadata information into an Excel file

