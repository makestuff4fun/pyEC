import pyb
import utime as ut
import struct

print("Initializing COM Port")
serial = pyb.UART(3, 115200)

# Flag saying wer are reading data
new_chunk = False  

buff = bytearray(11)
index = 0

# Full data chunk received?
good_data = False

# Delay for testing to allow serial data to arrive
# time.sleep(1)

ax, ay, az = (0,)*3
angvx, angvy, angvz = (0,)*3
angx, angy, angz = (0,)*3
magx, magy, magz = (0,)*3

#print("Entering Main Loop")

#implement timeout
def read_IMU_data():
    global ax, ay, az, angx, angy, angz, buff, index, good_data, new_chunk, serial
#    timeout = 0.0001
#    time_now = time.clock()
#    while ((time.clock() - time_now) < timeout and not good_data):
    timeout = ut.ticks_add(ut.ticks_us(), 800)

    while (ut.ticks_diff(timeout, ut.ticks_us())) > 0 and (not good_data):
#    while (not good_data):
        if serial.any():
            read_char = serial.read(1)
            #print(read_char)
        else:
            return
        
        if not new_chunk:
            # We are waiting for header byte
            if read_char == b'\x55':
                new_chunk = True
                buff[index] = ord(read_char)
                # print(buff[index])
                index += 1
                continue
                
        else:
            buff[index] = ord(read_char)
            # print(ord(read_char))
            index += 1
            
            if index >= 11:
                # reset & set OK to process flag
                index = 0
                new_chunk = False
                checksum = sum(buff[0:10])
                
                if checksum.to_bytes(2, 'big')[1] == buff[10]:
                    # Good data
                    good_data = True
            
    if good_data == True:
        good_data = False
        if buff[1] == b'\x50':
            # Time, not implemented
            pass
        elif buff[1] == 81:
            g = 9.81
            conv = 16.0 / 32768.0
            accel = struct.unpack("<hhh", buff[2:8])
            ax, ay, az = [a*conv for a in accel]
#            print('Acceleration', "ax: ", "{0:.2f}".format(ax), "ay: ", "{0:.2f}".format(ay), "az: ", "{0:.2f}".format(az))
#            temp = struct.unpack("<h", buff[8:10])
#            temp = temp[0] / 100.0
#            print("Temp: ", temp)
        elif buff[1] == 82:
            conv = 2000.0 / 32768.0
            angles = struct.unpack("<hhh", buff[2:8])
            angvx, angvy, angvz = [a*conv for a in angles]
#            print("Ang V", "angVx: ", "{0:.2f}".format(angvx), "angVy: ", "{0:.2f}".format(angvy), "angVz: ", "{0:.2f}".format(angvz))

        elif buff[1] == 83:
            conv = 180.0 / 32768.0
            angles = struct.unpack("<hhh", buff[2:8])
            angx, angy, angz = [a*conv for a in angles]
#            print("Angles", "angx: ", "{0:.2f}".format(angx), "angy: ", "{0:.2f}".format(angy), "angz: ", "{0:.2f}".format(angz))
        elif buff[1] == 84:
            conv = 1
            mag = struct.unpack("<hhh", buff[2:8])
            magx, magy, magz = [a*conv for a in mag]
#            print("Magnetic", "magx: ", "{0:.2f}".format(magx), "magy: ", "{0:.2f}".format(magy), "magz: ", "{0:.2f}".format(magz))
        
        return True
        
    else:    
        return False
    


    