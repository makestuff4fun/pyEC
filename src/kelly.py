import pyb

serial = pyb.UART(2, 19200)

# 3A
# TPS buf[2]
# Regen buf[3]
# volts buf[11]
# motor_temp buf[12]
# control_temp buf[13]

# 3B
# speed (256 * buf[4] + buf[5])
# amps amps = (256 * buf[6] + buf[7])

ch = b'\xFF'

speed = 0
volts = 0
amps = 0
motor_temp = 0
control_temp = 0
throttle = 0
regen = 0

def init():
    pass


def get_data():
#    start = ut.ticks_us()
#    // responses take 100us
    buf = bytearray(19)
    
    global speed, volts, amps, motor_temp, control_temp, regen, throttle
    
    # process all reads in the buffer:
    # buffer can hold 64
    # Sometimes it's messed up and this should clear it

    if serial.any() >= 19:
        serial.readinto(buf, 19)
        if buf[1] == 0x10:
            # print ("0x10")
            if buf[0] == 0x3A:
                # print ("0x3A")
                volts = buf[11]
                motor_temp = buf[12]
                control_temp = buf[13]
                regen = buf[3]
                throttle = buf[2]
            elif buf[0] == 0x3B:
                # print ("0x3B")
                speed = (256 * buf[4] + buf[5])
                amps = (256 * buf[6] + buf[7])

            elif buf[0] == 0x3C:
                # print ("0x3C")
                # buf = buf[2:]
                pass
            else:
                # bad data, clear the buffer
                print("Kelly Unknown Data Type, clearing buffer")
                serial.read(serial.any())
        else:
            print("Kelly bad header byte, clearing buffer")
            # bad data, clear the buffer
            #print(buf)
            serial.read(serial.any())
    else:
        # bad data clear the buffer
        # print("Kelly Expecting 19 bytes, clearing buffer")
        # print(buf)
        serial.read(serial.any())
    # Debug message    
    # print("Kelly Serial Time: ", ut.ticks_diff(ut.ticks_us(), start))

def send_3A():
    serial.write(b'\x3A\x00\x3A')
        
def send_3B():
    serial.write(b'\x3B\x00\x3B')

def send_3C():
    serial.write(b'\x3C\x00\x3C')



