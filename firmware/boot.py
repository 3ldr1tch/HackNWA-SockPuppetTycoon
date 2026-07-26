import storage
import usb_cdc

usb_cdc.enable(console=True, data=True)

# Explicitly export CIRCUITPY over USB.
storage.enable_usb_drive()

# Make the internal filesystem writable.
storage.remount("/", readonly=False)

print("Boot OK")
