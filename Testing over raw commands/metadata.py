import usb.core
import usb.util
import struct
import time
import pandas as pd
import os
import re
import pwd



def Inquiry1(ep_in, ep_out, dev):
    
    CBW_SIGNATURE_inq1 = 0x43425355
    CBW_TAG_inq1 = 0xdeadbeef
    CBW_LUN_inq1 = 0
    CBW_DATA_LEN_inq1 = 36  # Expected INQUIRY response size
    CBW_FLAGS_inq1 = 0x80   # Direction: IN (device to host)
    CBW_CB_LEN_inq1 = 6     # Length of SCSI command block

    # Standard INQUIRY Command Descriptor Block
    scsi_cmd = bytes([
        0x12,       # Operation Code: INQUIRY
        0x00,       # EVPD = 0 => standard inquiry
        0x00,       # Page Code = 0 (ignored when EVPD=0)
        0x00,       # Reserved
        CBW_DATA_LEN_inq1,  # Allocation length
        0x00        # Control
    ])
    scsi_cmd += bytes(16 - len(scsi_cmd))  # pad to 16 bytes

    # Construct CBW (Command Block Wrapper)
    cbw_inquiry = struct.pack("<I", CBW_SIGNATURE_inq1)
    cbw_inquiry += struct.pack("<I", CBW_TAG_inq1)
    cbw_inquiry += struct.pack("<I", CBW_DATA_LEN_inq1)
    cbw_inquiry += struct.pack("B", CBW_FLAGS_inq1)
    cbw_inquiry += struct.pack("B", CBW_LUN_inq1)
    cbw_inquiry += struct.pack("B", CBW_CB_LEN_inq1)
    cbw_inquiry += scsi_cmd[:16]

    assert len(cbw_inquiry) == 31, f"CBW must be 31 bytes, got {len(cbw_inquiry)}"


    ##print("Sending CBW (INQUIRY)...")
    dev.write(ep_out.bEndpointAddress, cbw_inquiry, timeout=1000)
    ##print("Reading response data...")
    start_time = time.time()
    data = dev.read(ep_in.bEndpointAddress, CBW_DATA_LEN_inq1, timeout=1000)
    end_time = time.time()
    ##print(f"Received {len(data)} bytes in {end_time - start_time:.6f} seconds")    
    
    #print("Raw INQUIRY Data:")
    #print(" ".join(f"{byte:02x}" for byte in data))



    # Optional: Parse vendor/product strings from INQUIRY response
    version = data[2]
    vendor = bytes(data[8:15]).decode(errors='ignore').strip()
    ##print(f"SCSI Version: {version:02x}")
    ##print(f"device type: {vendor}")
    device = bytes(data[16:31]).decode(errors='ignore').strip()
    ##print(f"Unit: {device}")
    time.sleep(1.0)
    try:
        ##print("Reading CSW (INQUIRY)...")
        cswi = dev.read(ep_in.bEndpointAddress, 16, timeout=5000)
        ##print("CSW (INQUIRY):", " ".join(f"{b:02x}" for b in cswi))
        ##print("Successfully received CSW for INQUIRY. Moving to next command.\n")

    except usb.core.USBError:
        dev.clear_halt(ep_in.bEndpointAddress)
        dev.clear_halt(ep_out.bEndpointAddress)
    devty = re.sub(r'[\x00-\x1F]', '', vendor)

    dinq1 = {
        "SCSI Version": version,
        "Vendor": devty,
        "Device": device
    }
    inq1 = pd.DataFrame([dinq1])

    return inq1

def Inquiry2(ep_in, ep_out, dev):
    
    CBW_SIGNATURE = 0x43425355
    CBW_TAG = 0xdeadbeef
    CBW_LUN = 0
    CBW_DATA_LEN = 24  # Expected INQUIRY response size
    CBW_FLAGS = 0x80   # Direction: IN (device to host)
    CBW_CB_LEN = 6     # Length of SCSI command block

    # Standard INQUIRY Command Descriptor Block
    scsi_cmd = bytes([
        0x12,       # Operation Code: INQUIRY
        0x01,       # EVPD = 0 => standard inquiry
        0x80,       # Page Code = 0 (ignored when EVPD=0)
        0x00,       # Reserved
        CBW_DATA_LEN,  # Allocation length
        0x00        # Control
    ])
    scsi_cmd += bytes(16 - len(scsi_cmd))  # pad to 16 bytes

    # Construct CBW (Command Block Wrapper)
    cbw_inquiry = struct.pack("<I", CBW_SIGNATURE)
    cbw_inquiry += struct.pack("<I", CBW_TAG)
    cbw_inquiry += struct.pack("<I", CBW_DATA_LEN)
    cbw_inquiry += struct.pack("B", CBW_FLAGS)
    cbw_inquiry += struct.pack("B", CBW_LUN)
    cbw_inquiry += struct.pack("B", CBW_CB_LEN)
    cbw_inquiry += scsi_cmd[:16]

    assert len(cbw_inquiry) == 31, f"CBW must be 31 bytes, got {len(cbw_inquiry)}"


    #print("Sending CBW (INQUIRY)...")
    dev.write(ep_out.bEndpointAddress, cbw_inquiry, timeout=1000)
    #print("Reading response data...")
    start_time = time.time()
    data = dev.read(ep_in.bEndpointAddress, CBW_DATA_LEN, timeout=1000)
    end_time = time.time()
    #print(f"Received {len(data)} bytes in {end_time - start_time:.6f} seconds")    
    
    #print("Raw INQUIRY Data:")
    #print(" ".join(f"{byte:02x}" for byte in data))



    # Optional: Parse vendor/product strings from INQUIRY response
    removablei = bool(data[1] & 0x80)
    additional_length = data[4]
    #print(f"Removable: {'Yes' if removablei else 'No'}")
    #print(f"Additional Length: {additional_length}")
    if data[1] == 0x80:
        page_length = data[3]
        serial = bytes(data[4:4 + page_length]).decode(errors='ignore').strip()
        #print(f"Unit Serial Number: {serial}")
    time.sleep(1.0)
    try:
        #print("Reading CSW (INQUIRY)...")
        csw = dev.read(ep_in.bEndpointAddress, 16, timeout=5000)
        #print("CSW (INQUIRY):", " ".join(f"{b:02x}" for b in csw))
        #print("Successfully received CSW for INQUIRY. Moving to next command.")

    except usb.core.USBError:
        dev.clear_halt(ep_in.bEndpointAddress)
        dev.clear_halt(ep_out.bEndpointAddress)

    dinq2 = {
"Removable": "Yes" if removablei else "No",
        "Serial": serial
    }
    inq2 = pd.DataFrame([dinq2])

    return inq2

def readcap(ep_in, ep_out, dev):

    scsi_cmd2 = bytes([
        0x25,               # READ CAPACITY (10)
        0x00,               # LUN
        0x00,0x00,0x00,0x00, # Logical Block Address (LBA)
        0x00,0x00,          # Reserved
        0x00,               #PMI
        0x00                # Control
        ]) + bytes(6)      # Pad to 16 bytes

    CBW_SIGNATURE2 = 0x43425355
    CBW_TAG2 = 0xdeadbe01
    CBW_LUN2 = 0
    CBW_DATA_LEN2 = 8 # Expected INQUIRY response size
    CBW_FLAGS2 = 0x80  # Direction: IN
    CBW_CB_LEN2 = 10  # Length of the command



    cbw_readcap = struct.pack("<I", CBW_SIGNATURE2)
    cbw_readcap += struct.pack("<I", CBW_TAG2)
    cbw_readcap += struct.pack("<I", CBW_DATA_LEN2)
    cbw_readcap += struct.pack("B", CBW_FLAGS2)
    cbw_readcap += struct.pack("B", CBW_LUN2)
    cbw_readcap += struct.pack("B", CBW_CB_LEN2)
    cbw_readcap += scsi_cmd2[:16]

    assert len(cbw_readcap) == 31, f"CBW must be 31 bytes, got {len(cbw_readcap)}"

    dev.write(ep_out.bEndpointAddress, cbw_readcap, timeout=1000)    
    data2= dev.read(ep_in.bEndpointAddress, CBW_DATA_LEN2, timeout=5000)
    total_blocks = struct.unpack(">I", data2[0:4])[0] + 1
    block_size = struct.unpack(">I", data2[4:8])[0]
    #print(f"Total blocks: {total_blocks}")
    #print(f"Block size: {block_size}")
    total_cap = total_blocks * block_size
    #print(f"Total capacity: {total_cap} bytes")

    csw2 = dev.read(ep_in.bEndpointAddress, 13, timeout=1000)
    #print("CSW (READ_CAP):", " ".join(f"{b:02x}" for b in csw2))
    #print("done")


    dread1 = {
        "Total Blocks": total_blocks,
        "Block Size": f'{block_size} bytes',
        "Total Capacity": f"{total_cap/(1024*1024*1024):.2f}GB"
    }
    read1 = pd.DataFrame([dread1])

    return read1


