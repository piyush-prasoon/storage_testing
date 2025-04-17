import struct
import time
import pandas as pd 


def read(ep_in,ep_out,dev,tot):
    # Constants
    CBW_SIGNATURE = 0x43425355
    CBW_TAG = 0xabcdef01
    CBW_FLAGS = 0x80  # Direction: IN
    CBW_LUN = 0       # Logical Unit Number
    CBW_CB_LEN = 10   # 10-byte SCSI command
    lba = 24576
    tot = 2
    block_size = 512
    data_cap = tot * 1024 * 1024 * 1024    # 4 GB
    data_blocks = data_cap // block_size
    max_read_cap = 20480  #10mb    
    remaining_blocks = data_blocks
    count = 1         
    starttime = time.time()
    latency = 0
    while remaining_blocks > 0:
        data_to_be_read = min(remaining_blocks, max_read_cap)
        print(f"READ ({count}/{(data_blocks // max_read_cap)+1}) , LBA : {lba}")

        # Construct READ(10) command
        read_cmd = bytes([
            0x28,  # READ(10) operation code
            0x00,  # Flags
            (lba >> 24) & 0xFF, (lba >> 16) & 0xFF, (lba >> 8) & 0xFF, lba & 0xFF,  # LBA
            0x00,  # Reserved
            (data_to_be_read >> 8) & 0xFF, data_to_be_read & 0xFF,  # Transfer length
            0x00   # Control
        ]) + bytes(6)  # Pad to 16 bytes for CBW

        # Construct CBW
        cbw = struct.pack("<I", CBW_SIGNATURE)  # CBW Signature
        cbw += struct.pack("<I", CBW_TAG)       # CBW Tag
        cbw += struct.pack("<I", block_size * data_to_be_read)  # Data transfer length
        cbw += struct.pack("B", CBW_FLAGS)      # Flags: IN
        cbw += struct.pack("B", CBW_LUN)        # LUN
        cbw += struct.pack("B", CBW_CB_LEN)     # CDB Length
        cbw += read_cmd[:16]                    # CDB (padded)

        assert len(cbw) == 31, "CBW must be 31 bytes"

        # Send CBW
        dev.write(ep_out.bEndpointAddress, cbw, timeout=1000)

        # Read data
        read_start_time = time.time()
        data = dev.read(ep_in.bEndpointAddress, block_size * data_to_be_read, timeout=20000)
        read_end_time = time.time()

        # Calculate and store latency
        latency += read_end_time - read_start_time

        # Read CSW
        csw = dev.read(ep_in.bEndpointAddress, 13, timeout=1000)
        print("CSW Response:", csw)
        # Update remaining blocks and LBA
        remaining_blocks -= data_to_be_read
        lba += data_to_be_read
        count += 1

    endtime = time.time()

    elapsed_time = endtime - starttime
    # Calculate read speed
    read_speed = (data_cap / 1024 / 1024) / elapsed_time  # Speed in MB/s
    print(f"Read {tot} GBS in {elapsed_time:.2f} seconds ({read_speed:.2f}) MB/s")
    print(f"Total Latency: {(latency/count)*1000:.2f} milliseconds")

    read_reps = {
        "read speed": f"{read_speed:2f} MB/s",
        "time taken to read": f"{elapsed_time:.2f} seconds",
        "Average read latency": f"{(latency/count)*1000:.2f} milliseconds"
    }

    rdat = pd.DataFrame(read_reps,index=[0])
    return rdat