import pandas as pd
import struct
import time
import os

def write(ep_in, ep_out, dev, tot):
    CBW_SIGNATURE = 0x43425355
    CBW_TAG = 0xabcdef01
    CBW_FLAGS = 0x00  # Direction: OUT (for writing)
    CBW_LUN = 0       # Logical Unit Number
    CBW_CB_LEN = 10   # 10-byte SCSI command
    lba = 24576
    latency = 0
    block_size = 512
    data_cap = tot * 1024 * 1024 * 1024  # 2 GB
    tot_data_blocks = data_cap // block_size
    max_write_cap = 20480 #10mb    
    remaining_blocks = tot_data_blocks
    count = 1         
    remaining_blocks = tot_data_blocks
    write_data = os.urandom(block_size * max_write_cap)  # Random data
    starttime = time.time()
    while remaining_blocks > 0:
        data_to_be_written = min(remaining_blocks, max_write_cap)
        print(f"write ({count}/{(tot_data_blocks // max_write_cap)+1}) , LBA : {lba}")

        # Construct write(10) command
        write_cmd = bytes([
            0x2A,  # WRITE(10) operation code
            0x00,  # Flags
            (lba >> 24) & 0xFF, (lba >> 16) & 0xFF, (lba >> 8) & 0xFF, lba & 0xFF,  # LBA
            0x00,  # Reserved
            (data_to_be_written >> 8) & 0xFF, data_to_be_written & 0xFF,  # Transfer length
            0x00   # Control
        ]) + bytes(6)  # Pad to 16 bytes for CBW

        # Construct CBW
        cbw = struct.pack("<I", CBW_SIGNATURE)  # CBW Signature
        cbw += struct.pack("<I", CBW_TAG)       # CBW Tag
        cbw += struct.pack("<I", block_size * data_to_be_written)  # Data transfer length
        cbw += struct.pack("B", CBW_FLAGS)      # Flags: IN
        cbw += struct.pack("B", CBW_LUN)        # LUN
        cbw += struct.pack("B", CBW_CB_LEN)     # CDB Length
        cbw += write_cmd[:16]                    # CDB (padded)
        assert len(cbw) == 31, "CBW must be 31 bytes"
        
        # Send CBW
        dev.write(ep_out.bEndpointAddress, cbw, timeout=1000)
        # write data
        write_start_time = time.time()
        data = dev.write(ep_out.bEndpointAddress, write_data[:block_size * data_to_be_written], timeout=20000)
        write_end_time = time.time()

        # Calculate and store latency
        latency += write_end_time - write_start_time

        # write CSW
        csw = dev.read(ep_in.bEndpointAddress, 13, timeout=1000)
        print("CSW Response:", csw)

        # Update remaining blocks and LBA
        remaining_blocks -= data_to_be_written
        lba += data_to_be_written
        count += 1

    endtime = time.time()

    elapsed_time = endtime - starttime
    # Calculate write speed
    write_speed = (data_cap / 1024 / 1024) / elapsed_time  # Speed in MB/s
    print(f"write {tot} GBS in {elapsed_time:.2f} seconds ({write_speed:.2f}) MB/s")
    print(f"Total Latency: {(latency/count)*1000:.2f} milliseconds")
    
    write_reps = {
        "write speed": f"{write_speed:.2f} MB/s",
        "time taken to write": f"{elapsed_time:.2f} seconds",
        "Average write latency": f"{(latency/count)*1000:.2f} milliseconds",
    }
    wdat = pd.DataFrame(write_reps, index=[0])
    return wdat