import struct


def clear(ep_in, ep_out, dev, tot):
    # Constants
    CBW_SIGNATURE = 0x43425355
    CBW_TAG = 0xabcdef01
    CBW_FLAGS = 0x00  # Direction: OUT (for writing)
    CBW_LUN = 0       # Logical Unit Number
    CBW_CB_LEN = 10   # 10-byte SCSI command
    lba = 24576
    block_size = 512
    data_cap = tot * 1024 * 1024 * 1024 # Total data to clear (in bytes)
    data_blocks = data_cap // block_size
    max_write_cap = 20480  # 10MB per write operation
    remaining_blocks = data_blocks
    count = 1         
    overwrite_data = bytes(block_size * max_write_cap)  # All zeros
    remaining_blocks = data_blocks

    while remaining_blocks > 0:
        # Determine how many blocks to write
        data_to_be_written = min(remaining_blocks, max_write_cap)
        print(f"WRITE ({count}/{(data_blocks // max_write_cap) + 1}), LBA: {lba}")

        # Construct WRITE(10) command
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
        cbw += struct.pack("B", CBW_FLAGS)      # Flags: OUT (for write)
        cbw += struct.pack("B", CBW_LUN)        # LUN
        cbw += struct.pack("B", CBW_CB_LEN)     # CDB Length
        cbw += write_cmd[:16]                   # CDB (padded to 16 bytes)
        assert len(cbw) == 31, "CBW must be 31 bytes"

        # Send CBW
        dev.write(ep_out.bEndpointAddress, cbw, timeout=1000)

        # Write zeroed data
        dev.write(ep_out.bEndpointAddress, overwrite_data[:block_size * data_to_be_written], timeout=20000)

        # Read CSW (Check Status Wrapper)
        csw = dev.read(ep_in.bEndpointAddress, 13, timeout=1000)
        print("CSW Response:", csw)

        # Update LBA and remaining blocks
        lba += data_to_be_written
        remaining_blocks -= data_to_be_written
        count += 1

    print("All data cleared")





 
   
