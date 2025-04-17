import usb.core
import usb.util
import pandas as pd
import time
from write import write 
from clear import clear
from read import read

# Find the USB device (adjust VID/PID if needed)
dev = usb.core.find(idVendor=0x0781, idProduct=0x5591)
if dev is None:
    raise ValueError("Device not found")
print("Device found!")

# Detach kernel driver if needed
reattach = False
if dev.is_kernel_driver_active(0):
    dev.detach_kernel_driver(0)
    reattach = True
    time.sleep(0.5)

dev.set_configuration()
cfg = dev.get_active_configuration()

# Locate Mass Storage interface
intf = None
for i in cfg:
    if i.bInterfaceClass == 0x08:  # Mass Storage
        intf = i
        break

if intf is None:
    raise RuntimeError("No Mass Storage interface found")

intf_number = intf.bInterfaceNumber

# Find Bulk IN/OUT endpoints
ep_in = usb.util.find_descriptor(
    intf,
    custom_match=lambda e: (
        usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN and
        (e.bmAttributes & 0x3) == 2
    )
)
ep_out = usb.util.find_descriptor(
    intf,
    custom_match=lambda e: (
        usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT and
        (e.bmAttributes & 0x3) == 2
    )
)

if ep_in is None or ep_out is None:
    raise ValueError("Could not find bulk IN/OUT endpoints")

#CALLING WRITE AND READ FUCNTIONS
try:
    tot = 2
    rep = {
        "size of data ": f"{tot} GB",
    }
    reads = pd.DataFrame(rep, index=[0])
    w_data = write(ep_in, ep_out, dev, tot)
    r_data = read(ep_in, ep_out, dev, tot)
    report = pd.concat([reads , w_data, r_data], axis=1)
    with pd.ExcelWriter('test_report.xlsx') as writer:
        report.to_excel(writer, sheet_name='Testing', index=False)
        print("Data written to report.xlsx")
    clear(ep_in, ep_out, dev, tot)
    

 
except usb.core.USBError as e:
    print("USB Error:", e)
    try:
        dev.clear_halt(ep_in.bEndpointAddress)
        dev.clear_halt(ep_out.bEndpointAddress)
        print("Cleared endpoint stalls.")
        reattach = True
    except Exception as e2:
        print("Failed to clear endpoint halt:", e2)
 
#CLEAN UP PHASE
finally:
    try:
        usb.util.release_interface(dev, intf_number)
        if reattach:
            dev.attach_kernel_driver(intf_number)
        print("Released interface and cleanup done.")
    except Exception as cleanup_error:
        print("Cleanup error:", cleanup_error)