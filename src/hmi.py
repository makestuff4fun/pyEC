############################
# Imports
import pyb
import utime as ut

# debug("Init Start")

# debug("Opening Serial")
serial = pyb.UART(4, 115200)

PAGE_MAIN = 0
PAGE_PASSWORD = 1
PAGE_MAIN_MENU = 2
PAGE_GRAPH = 3
PAGE_GRAPH_MENU = 4
PAGE_LOG_GRAPH = 5
PAGE_LOGS = 6
PAGE_CHANNELS = 7
PAGE_GPS = 8
PAGE_GPS_ERR = 9
PAGE_KELLY = 10
PAGE_TIME_DATE = 11
PAGE_BINARY = 12
PAGE_NUMBER = 13
PAGE_DEBUG = 14
PAGE_SAVED_ELEMENTS = 15
PAGE_MENU2 = 16

ID_GRAPH = 1

CHANNEL_RED = 0
CHANNEL_GREEN = 1
CHANNEL_BLUE = 2
CHANNEL_YELLOW = 3

# Assume page main
# This should be changed if password screen is used
# at which point a call to get_page() should be used
page = PAGE_MAIN

return_bytes = []

speed = 0
speed_values = []
speed_samples = 5

volts = 95
volts_values = []
volts_samples = 10

amps = 0
amps_values = []
amps_samples = 10

#Average value
motor_temp = 35
#list of values
motor_temp_values = []
# Number of values to average
motor_temp_samples = 50

throttle = 0
regen = 0
light = 0
key = 0

graph_channel = 0

# debug("Init Complete")

def debug(msg, arg='', arg2='', arg3=''):
    # Comment out print line to disable debug messages
    # change print to second serial if messages should be sent
    # to output other than REPL prompt
    print(msg, arg, arg2, arg3)
    pass

def write_raw(message):


    # Temporary cludge to fix errors. Clearing this data certainly is
    # missing a page update or other command, button push, graph index etc.
    # I'm just not sure where to force the processing to occur. Trade off
    # between current command not working and a button having to be pushed
    # again etc. I will work on a permanent fix.
#    if serial.any():
        #basically flush the buffer
#        serial.read()
    serial.write(message)

def write_message(message):
    # All Errors are processed from calling function, for now.
    # I'm not sure the best location of put this code. There is a chance
    # there is code waiting to be read, which will likely screw up our
    # command.
    message = message.encode("ISO-8859-1")
    message += b"\xFF\xFF\xFF"
    write_raw(message)
    
def set(key, value):
    debug("Setting Key: ", key, value)
    message = key + '=' + str(value)
    write_message(message)

#    return process_standard_return()
    
def set_page(id):
    page = id
    debug("Set Page by Id: ", id)
    write_message('page ' + str(id))

#    return process_standard_return()
    
def set_value(id, value):
#    debug("Setting Value: ", id, value)
    write_message(str(id) + '.val=' + str(value))

#    return process_standard_return()

def set_text(id, value):
    debug("Setting Text: ", id, value)
    write_message(str(id) + '.txt="' + str(value) + '"')

#    return process_standard_return()
    
def read_return():
    # reset Return Buffer
    # The read function could return a value
    # This is better in some ways, but I would prefer to be able to access
    # the raw data if I want for debugging and it's arguably an object
    # property anyway
    global return_bytes, timeout
    return_bytes = []

    count = 0
    timeout = ut.ticks_add(ut.ticks_us(), 600)
    while (ut.ticks_diff(timeout, ut.ticks_us())) > 0:
#    while(1):
        read_byte = serial.read(1)
        
        if read_byte is None or read_byte == b"":
            continue

        read_char = read_byte[0]

        if read_char == 0xff and not return_bytes:
            continue

        # This seems wrong, I need zeros too...
#            if readChar != 0x00:
        return_bytes.append(read_char)

            # max bytes to read. Not sure how useful this is
            # perhaps speed up code if length of return is known.
            # to simplify the readReturn function, I'm leaving it disabled
            # if len(bytes_buf) == 5:
            #     break

        if read_char == 0xff:
            count = count + 1
            if count == 3:
                #debug("Return Bytes True: ", return_bytes)
                return True
        else:
            count = 0

    # Return value is read, or returned Error
    # Interpret Return Value
    if return_bytes == []:
        # Nothing Read
        debug("No response from hardware!")
        return False
    else:
#        debug("HMI Serial time: ", ut.ticks_diff(timeout, ut.ticks_us()))
        debug("Return Bytes False: ", return_bytes)
        return False

def process_return():

    ERRORS = {
        0x00 : "Invalid instruction",
        #0x01 : "Successful execution of instruction",
        0x02 : "Component ID invalid",
        0x03 : "Page ID invalid",
        0x04 : "Picture ID invalid",
        0x05 : "Font ID invalid",
        0x11 : "Baud rate setting invalid",
        0x12 : "Curve control ID number or channel number is invalid",
        0x1A : "Variable name invalid",
        0x1B : "Variable operation invalid",
        0x1C : "Failed to assign",
        0x1D : "Operate EEPROM failed",
        0x1E : "Parameter quantity invalid",
        0x1F : "IO operation failed",
        0x20 : "Undefined escape characters",
        0x23 : "Too long variable name",
        }

    MESSAGES = {
        0x01 : "Successful execution of instruction",
        0x65 : "Touch event return data",
        0x66 : "Current page ID number returns",
        0x67 : "Touch coordinate data returns",
        0x68 : "Touch Event in sleep mode",
        0x70 : "String variable data returns",
        0x71 : "Numeric variable data returns",
        0x86 : "Device automatically enters into sleep mode",
        0x87 : "Device automatically wake up",
        0x88 : "System successful start up",
        0x89 : "Start SD card upgrade",
        0xFE : "Data transparent transmit start",
        0xFD : "Data transparent transmit finished",
        }

    global return_bytes, page
    
    # We got some return Data, let's process it
    if (read_return()):
#            debug('Return Bytes: ', return_bytes)

        # 0X65    Touch event return data
        # 0X66    Current page ID number returns
        # 0X67    Touch coordinate data returns
        # 0X68    Touch Event in sleep mode
        # 0X70    String variable data returns
        # 0X71    Numeric variable data returns
        # 0X86    Device automatically enters into sleep mode
        # 0X87    Device automatically wake up
        # 0X88    System successful start up
        # 0X89    Start SD card upgrade
        # 0XFE    Data transparent transmit start
        # 0XFD    Data transparent transmit finished

        # Technically not needed. Left over from trimming only copy of
        # return buffer. I'll leave it because makes code more readable
        code_byte = return_bytes[0]

        if code_byte in ERRORS:
            #debug("ERROR: " + ERRORS[int(code_byte)], hex(code_byte))
            
            if code_byte == 0x12:
                # If page already is main, the problem is already fixed
                # No need to output anything
                if page != PAGE_MAIN:
                    debug("Page Out of sync, syncing to main")
                    page = PAGE_MAIN
                    get_page()
                
            return False

        elif code_byte in MESSAGES:
            # debug("MESSAGE: " + MESSAGES[int(code_byte)], hex(code_byte))
            pass
            
        else:
            # Could also be unimplemented return code
            # Verify using debug output
            debug('Unknown return code: ', code_byte)
            return False

        expected_postfix = [255, 255, 255]
        # This shouldn't happen as read code waits for trailing 0xFF
        # In fact, there is really no need to add them to the buffer just
        # to remove them later. But the current logic works, so I'll leave
        # it alone for now.
        if return_bytes[-3:] != expected_postfix:
            # debug("Response missing trailing bytes: ", return_bytes[-3:])
            debug("Response missing trailing bytes: ", code_byte)
            return False

        # Truncate the type and postfix
        # needed for Number and String return Data
        # Move to those locations only?
        trimmed_bytes = return_bytes[1:-3]

        if code_byte == 0x01:
            # Nothing to be done, command succesfful
            return True

        elif code_byte == 0x65:  # Touch event return data
            # Implement when needed
            return True

        elif code_byte == 0x66:  # Current page ID number returns
            page = return_bytes[1]
            debug('Current Page:', page)
            return True

        elif code_byte == 0x67:  # Touch coordinate data returns
            # Implement when needed
            return True

        elif code_byte == 0x68:  # Touch Event in sleep mode
            # Implement when needed
            return True

        elif code_byte == 0x70:  # String variable data returns
            # Added for readability
            trimmed_bytes = return_bytes[1:-3]

            #Format String
            strb = "".join([chr(b) for b in trimmed_bytes])

            # Consider if this method to return string is OK
            # alternately set string in Class properties
            # since Empty string is False, non empty True
            # This can still work. Ok for  now
            debug("Text: ", strb)
            return strb

        elif code_byte == 0x71:  # Numeric variable data returns
            trimmed_bytes = return_bytes[1:-3]
            # convert to big endian
            trimmed_bytes = trimmed_bytes[::-1]
            num = 0
            # from github micropython discussion
            # works but it's magic to me!
            for x in trimmed_bytes:
                num <<= 8
                num |= x
    
            #debug("Trimmed_bytes: ", trimmed_bytes)
            
            #num = int.from_bytes(trimmed_bytes, 'little')
            
            #debug("Number: ", num)
            return num
            #return 0
            
        elif code_byte == 0x86:  # Device automatically enters sleep mode
            # Implement when needed
            return True

        elif code_byte == 0x87:  # Device automatically wake up
            # Implement when needed
            return True

        elif code_byte == 0x88:  # System successful start up
            # Implement when needed
            return True

        elif code_byte == 0x89:  # Start SD card upgrade
            # Implement when needed
            return True

        elif code_byte == 0xfd:  # Data transparent transmit finished
            # Have to consiser returning True or code_byte
            return code_byte

        elif code_byte == 0xfe:  # Data transparent transmit Start
            # Have to consiser returning True or code_byte
            return code_byte

        else:
            # Should never get here as fbyte is checked for validity above
            debug("Response Error with unknown code: ",code_byte)
            return False
    else:
        # readReturn Failed
        return False

def process_standard_return():
    # Check for return value
    if serial.any():
        # This should only indicate an Error, so fetch it
        return process_return()
    else:
        # No debug Success message has been generated
        # We can add one here
        # debug("Success by lack of Error")
        return True
        
def set_page_by_name(page_name):
    # This will not update the class page variable as we don't know what
    # id goes with page_name. my specific HMI code does a "sendme" on each
    # page load that will account for this. Perhaps you want the same or
    # a page to id dictionary
    debug("Set Page by Name: ", page_name)
    write_message('page ' + page_name)

#    return process_standard_return()

def get_page():
    debug('Get current page')
    write_message('sendme')

    # Give Nextion time to reply
    timeout = ut.ticks_add(ut.ticks_ms(), 50)
    while (ut.ticks_diff(timeout, ut.ticks_ms())) > 0:
        if serial.any():
            return process_return()
    
    return False
     
def get(name):
    #debug("Get: ",name)
    write_message('get %s' % name)
    
    # Give Nextion time to reply
    timeout = ut.ticks_add(ut.ticks_ms(), 50)
    while (ut.ticks_diff(timeout, ut.ticks_ms())) > 0:
        if serial.any():
            return process_return()
    
    return False

def get_value(id):
    # There is an issue that there could be data waiting, what to do about
    # that? We can clear it, or process it. Most likely data is new page id
    # if we set the page we can ignore it. other data we should return
    # false, force calling function to process it or process it from here
    # not sure which is best. For now, call is_data()
    debug("Get Value: ",id)
    write_message('get %s.val' % id)
    return process_return()

def get_text(id):
    debug("Get Text: ", id)
    write_message('get %s.txt' % id)
    return process_return()

def add(id, channel, value):
    msg = "add " + str(id) + "," + str(channel) + "," + str(value)
    # debug(msg)
    write_message(msg)

    # only returns a value on Error
#    if (serial.any()):
        # To log the error to Debug console
#        return process_return()
#    else:
        # debug("Success by lack of Error")
    return True

def addt(id=1, channel=0, num_bytes=5, buff=None):
    debug("Bulk Graph", id, channel, num_bytes)
    write_message('addt ' + str(id) +',' + str(channel) + ',' + str(num_bytes))
    ret = process_return()
    if ret != 0xFE:
        debug("Invalid Start Code Received: ", ret)
        return ret
    else:
        debug("Start Raw Data OK")

    #Nextion needs 5ms to be ready for raw data, give 6ms
    ut.sleep_ms(6)

    if buff == None:
        buff = b'\x10\x10\x10\x10\x10'

#        debug("Raw Data: ", buff[:num_bytes])
    write_raw(buff[:num_bytes])
    ret = process_return()
    if ret != 0xFD:
        debug("Invalid End Code Received: ", ret)
    else:
        debug("End Raw Data OK")
        
def clear_graph(id=1):
    debug("Clearing Graph")
    write_message("cle "+ str(id) +",255")

    return process_standard_return()
        
def debug_message(str):
    # Set debug Text on Nextion Debug Page
    # Change page to debug page
    set_text("debug.message",str)
    set_page_by_name('debug')

def update_volts(new_volts):
    global volts, volts_values, volts_samples

    # add new sample
    volts_values.append(new_volts)
    
    # if more than desired samples, remove the oldest (item 0)
    if len(volts_values) > volts_samples:
        volts_values.pop(0)
        # calculate average
        volts = int(sum(volts_values)/volts_samples)
    else:
        # calculate average 
        volts = int(sum(volts_values)/len(volts_values))
    
def update_motor_temp(new_motor_temp):
    global motor_temp, motor_temp_values, motor_temp_samples
    
    # add new sample
    motor_temp_values.append(new_motor_temp)
    
    # if more than desired samples, remove the oldest (item 0)
    if len(motor_temp_values) > motor_temp_samples:
        motor_temp_values.pop(0)
        # calculate average
        motor_temp = int(sum(motor_temp_values)/motor_temp_samples)
    else:
        # calculate average 
        motor_temp = int(sum(motor_temp_values)/len(motor_temp_values))
        
def update_amps(new_amps):
    global amps, amps_values, amps_samples

    # add new sample
    amps_values.append(new_amps)
    
    # if more than desired samples, remove the oldest (item 0)
    if len(amps_values) > amps_samples:
        amps_values.pop(0)
        # calculate average
        amps = int(sum(amps_values)/amps_samples)
    else:
        # calculate average 
        amps = int(sum(amps_values)/len(amps_values))
        
def update_speed(new_speed):
    global speed, speed_values, speed_samples

    # add new sample
    speed_values.append(new_speed // 16)
    
    # if more than desired samples, remove the oldest (item 0)
    if len(speed_values) > speed_samples:
        speed_values.pop(0)
        # calculate average
        speed = int(sum(speed_values)/speed_samples)
    else:
        # calculate average 
        speed = int(sum(speed_values)/len(speed_values))
        
def update_page():
    # depends on current page
    global volts, amps, motor_temp, throttle, regen, speed
    if page == PAGE_PASSWORD:
        pass

    elif page == PAGE_MAIN:
        set_value('main.volts', volts)
        set_value('main.amps', amps)
        
        # motor_temp sensor reads a bit high, adjust
        mt = motor_temp - 10
        if mt < 0:
            mt = 0
        set_value('main.temp', mt)
        set_value('main.speed', speed)
        
        if volts <= 75:
            # Very low, in red
            # 70 = 0
            # 75 = 20
            bat = (volts - 70) * 4
            if bat < 0:
                bat = 0
        elif volts > 75 and volts <= 80:
            # yellow 20%
            bat = (volts - 75) * 4 + 20
        elif volts >= 98:
            bat = 100
        else:
            bat = int((volts - 75.0) * 4.454)
            if bat > 100:
                bat = 100
        
        set_value('main.bm', bat)

        cell_avg = 100 * volts // 24
        set_value('main.cell_avg', cell_avg)
        
        # Headlight symbol
        set_value('main.hl', light)
        
        
    elif page == PAGE_GRAPH:
        set_value('main.volts', volts)
        set_value('main.amps', amps)
        
        # motor_temp sensor reads a bit high, adjust
        mt = motor_temp - 10
        if mt < 0:
            mt = 0
        set_value('main.temp', mt)
        set_value('main.speed', speed)
    
    elif page == PAGE_KELLY:
        pass
        # print (buf3A)
        # print (buf3B)
#        for x in range(16):
#            tempString = 'na' + str(x) + '.val=' + str(buf3A[x])
#            send(tempString)
#            sendFF()
            # print (tempString)

#        tempString = 'nb3.val=' + str((256 * buf3B[2] + buf3B[3]))
#        send(tempString)
#        sendFF()
        # print (tempString)

#        tempString = 'nb5.val=' + str(256 * buf3B[4] + buf3B[5])
#        send(tempString)
#        sendFF()
        # print (tempString)
              
    else:
        pass
        
def update_graph():
    global volts, amps, motor_temp, throttle, regen, speed, graph_channel

        # add graphind code here
        # values between 0 and 255 ONLY

    if graph_channel == CHANNEL_RED:
        # Voltage is RED Channel 0
        # max is 103
        graph_volts = int(volts * 255 / 100)
#       graph_volts = 50

        if graph_volts > 255:
            graph_volts = 255

        add(ID_GRAPH, CHANNEL_RED, graph_volts)
    
    elif graph_channel == CHANNEL_GREEN:    
        # Amps max = 400     
        graph_amps = int(amps * 255 / 400)
#        graph_amps = 100

        if graph_amps > 255:
            graph_amps = 255

        add(ID_GRAPH, CHANNEL_GREEN, graph_amps)

    elif graph_channel == CHANNEL_BLUE:
        # Temp max = 150
        graph_temp = int(motor_temp * 255 / 150)
#        graph_temp = 20
        
        if graph_temp > 255:
            graph_temp = 255

        add(ID_GRAPH, CHANNEL_BLUE, graph_temp)

    elif graph_channel == CHANNEL_YELLOW:
        # Speed max = 100
        graph_speed = int(speed * 255 / 100)
#        graph_speed = 150
        
        if graph_speed > 255:
            graph_speed = 255
        
        add(ID_GRAPH, CHANNEL_YELLOW, graph_speed)

    # Increment channel to update
    graph_channel = graph_channel + 1
    if graph_channel > 3:
        graph_channel = 0