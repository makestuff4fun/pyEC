# boot.py -- run on boot-up
# can run arbitrary Python, but best to keep it minimal
import pyb

# pyb.main('main.py') # main script to run after this one
# pyb.usb_mode('VCP+MSC') # act as a serial and a storage device
# pyb.usb_mode('VCP+HID') # act as a serial device and a mouse

pyb.usb_mode('CDC')
pyb.main('main.py')


# pyb.usb_mode('CDC+MSC')
# pyb.main('cardreader.py')
# pyb.main('datalogger.py')
# pyb.main('main.py')
