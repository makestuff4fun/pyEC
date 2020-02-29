# main.py -- put your code here!
import micropython
from pyb import LED
from pyb import Pin
from pyb import DAC
from pyb import UART
from pyb import Timer
from pyb import RTC
from struct import *
import utime as ut
import utime
import pyb
import hmi
import kelly
import imu
import uio

# Needed to get error messages during interupt callbacks
micropython.alloc_emergency_exception_buf(100)

rtc = pyb.RTC()

# Timers for scheduling tasks
# Timer(2) and Timer(3) are only used for PWM of LED(3) and LED(4)
# Timer(5) controls the servo driver
# Timer(6) is used for timed ADC/DAC reading/writing
hmi_timer = pyb.Timer(2)
tick_timer = pyb.Timer(3)
kelly_timer = pyb.Timer(4)
switch_timer = pyb.Timer(5)
graph_timer = pyb.Timer(7)
log_timer = pyb.Timer(8)
imu_timer = pyb.Timer(9)


kelly_read = True # True = Read, False = Write
kelly_3A = True # True = 3A, False = 3B
request_kelly_data = False
read_kelly_data = False

# Bunch-O-Flags for scheduling tasks
# Time events, increase frequency and perhaps use different timers, not
# Flags with states

update_hmi = False
update_graph = False
update_imu = False
update_log = False
update_switch = False

ticks = 50

filename = ''

def hmi_tick(hmi_timer):
    global update_hmi
    update_hmi = True

def kelly_tick(kelly_timer):
    global kelly_read, request_kelly_data, read_kelly_data
    
	# Kelly updates fairly fast now. About 100us per read
	# slow downs and errors were all due to waiting for HMI
	# to send response codes. 
    
    if (kelly_read):
        request_kelly_data = True
    else:
        read_kelly_data = True
    
    kelly_read = not kelly_read

def tick(tick_timer):
    global ticks
    ticks = ticks + 1
      
def graph_tick(graph_timer):
    global update_graph
    update_graph = True

def imu_tick(imu_timer):
    global update_imu
    update_imu = True
    
def log_tick(log_timer):
    global update_log
    update_log = True

def switch_tick(switch_timer):
    global update_switch
    update_switch = True
    
#################### Setup 
# Needs to be global
# Setup
# Set Pins to correct state

# Inputs
user_switch = pyb.Switch()

left_turn_switch = Pin(Pin.cpu.B12, Pin.IN)
right_turn_switch = Pin(Pin.cpu.B13, Pin.IN)
brake_switch = Pin(Pin.cpu.C5, Pin.IN)
headlight_switch = Pin(Pin.cpu.B5, Pin.IN)
horn_switch = Pin(Pin.cpu.B2, Pin.IN)
key_switch = Pin(Pin.cpu.C13, Pin.IN)

# ADC Inputs
throttle_in = pyb.ADC(Pin.cpu.A6)
regen_in = pyb.ADC(Pin.cpu.A7)

# Outputs
# Conflict with Key (Kelly v1.0)
# buzzer = Pin(Pin.cpu.B0, Pin.OUT_PP)

pyb_red_led = LED(1)
pyb_green_led = LED(2)
pyb_blue_led = LED(4)

horn = Pin(Pin.cpu.C0, Pin.OUT_PP)
headlight = Pin(Pin.cpu.C1, Pin.OUT_PP)
key = Pin(Pin.cpu.B0, Pin.OUT_PP)

# DAC
throttle_out = DAC(1, bits=12)
regen_out = DAC(2, bits=12)

# Other
bike_on = False
light_on = False
horn_on = False

############### END PIN SETUP

def init():
    # print("Initialize Buzzer")
    # buzzer.low()

    print("Initialize LEDs")
    pyb_red_led.off()
    pyb_green_led.off()
    pyb_blue_led.off()

    print("Initialize Horn")
    # high is off
    horn.high()

    print("Initialize Headlight")
    # high is off
    headlight.high()

    print("Initialize DAC")
    throttle_out.write(0)
    regen_out.write(0)

    print("Initialize Key")
    # High is off
    # key.high()

    if key_switch.value():
        bike_on = True

    setup_rtc()

    # Check Bike / Switch State
    if key_switch.value():
        bike_on = True
        hmi.set('sleep',0)
        filename = '/sd/logs/' + get_datetime_filename() + '.csv'
        log = uio.open(filename,'w')
        log.write('date,time,volts,amps,speed,temp,throttle,regen,ax,ay,az,angx,angy,angz\n')
        print('Log: ' + filename + ' open')

        if headlight_switch.value():
            light_on = True
            hmi.light = 1
            headlight.low()
            
    # We just got power to the PyBoard but the bike
    # key is off. Make sure HMI is sleeping
    # Turn off light & horn
    else:
        bike_on = False
        hmi.set('sleep',1)
        light_on = False
        hmi.light = 0
        headlight.high()

    # This currently always sets the page to main
    # but we need to be synced with the display or updates won't work
    # Alternately we could get_page() and this should be done if we use passwords
    # Not sure what happens here if HMI is sleeping.
    # HMI Should be on? This might not work during sleep mode
    hmi.set_page(hmi.page)

    # Not needed as it's stored in HMI
    # 3 is always respond which seems perfect but in practice it's simply too slow
    # 2 is respond only on error which is good for debugging
    # 1 is respond only on success
    # 0 is never respond is best as errors are only used during debugging
    #   with a computer, not during general use
    # hmi.set('bkcmd', 2) 
    
def get_datetime_string():
    dt = rtc.datetime()
    dt_string = str(dt[0]) + "-"
    dt_string += '{:02d}'.format(dt[1]) + "-"
    dt_string += '{:02d}'.format(dt[2]) + "," 
    dt_string += '{:02d}'.format(dt[4]) + ":" 
    dt_string += '{:02d}'.format(dt[5]) + ":" 
    dt_string += '{:02d}'.format(dt[6]) 
    dt_string += '{:.4f}'.format(dt[7]/255)[1:]
    
#    print("dt: ", dt_string)
    return dt_string

def get_datetime_filename():
    dt = rtc.datetime()
    dt_string = str(dt[0])
    dt_string += '{:02d}'.format(dt[1])
    dt_string += '{:02d}'.format(dt[2]) 
    dt_string += '{:02d}'.format(dt[4]) 
    dt_string += '{:02d}'.format(dt[5]) 
    dt_string += '{:02d}'.format(dt[6]) 
    
#    print("dt: ", dt_string)
    return dt_string

def setup_rtc():
    # hmi.get() waits 50ms for a response
    # Avoid using it during main loop execution
    # get works during HMI sleep mode
    rtc0 = hmi.get('rtc0')
    rtc1 = hmi.get('rtc1')
    rtc2 = hmi.get('rtc2')
    rtc3 = hmi.get('rtc3')
    rtc4 = hmi.get('rtc4')
    rtc5 = hmi.get('rtc5')

    # Setup pyboard RTC

    rtc.datetime([rtc0, rtc1, rtc2, 0, rtc3, rtc4, rtc5, 0])
    #print("rtc: ", rtc.datetime())
    #Output the startup time as counted by HMI
    # prints the pyboard startup time.
    print(get_datetime_string())
    #print(get_datetime_filename())
    
# Start Main Code
init()

# Move to update_log location
# Have to start a new log file, if the bike is On
# filename = './logs/' + get_datetime_filename() + '.bin'    
# filename = '/sd//' + get_datetime_filename() + '.csv'    

# Initialize Timers

# 16.5ms / call
# 250ms / sec
hmi_timer.init(freq=15)
hmi_timer.callback(hmi_tick)

# 30 calls @ 2ms / 2 calls
# 30 ms / sec
kelly_timer.init(freq=30)
kelly_timer.callback(kelly_tick)

# 40 calls = 20Hz with Accel & Angle
# 1ms / call
# 40ms / sec
imu_timer.init(freq=40)
imu_timer.callback(imu_tick)

# 10ms ticks
tick_timer.init(freq=100)
tick_timer.callback(tick)

# 3ms / call
# 180ms / sec
graph_timer.init(freq=60)
graph_timer.callback(graph_tick)

# Has not been timed yet
log_timer.init(freq=4)
log_timer.callback(log_tick)

# Has not been timed yet
# This has the added effect of debouncing?
# Old debounce was 5 ticks @ 10ms each
# switch_tick is 50ms
# Tested it and it seems OK
# I'll leave the bebounce for now, test this riding for a while
switch_timer.init(freq=20)
switch_timer.callback(switch_tick)

# Total about 500ms / sec used
# Should be enough to add logging and some other stuff
# some things may be able to be optamized but a lot 
# is serial writes which are relatively Slow

print("Entering Main Loop")

while True:
    # Update Watchdog timer
    # Poll switches
    # Good enough for testing purposes
    # Can use interupts later
#    print(ticks)
#    print (imu.ax, imu.ay, imu.az)

    # Start Timer Tick Handlers
    if (update_switch):
        if (key_switch.value()) and (ticks > 5):
            # Add code to do when bike turns one
            # Turn on HMI
            # Turn on Logging etc.
            if not bike_on:
                hmi.set('sleep',0)
                bike_on = True
                filename = '/sd/logs/' + get_datetime_filename() + '.csv'
                log = uio.open(filename,'w')
                print('Log: ' + filename + ' open')
                log.write('date,time,volts,amps,speed,temp,throttle,regen,ax,ay,az,angx,angy,angz\n')
                ticks = 0
                
        if (not key_switch.value()) and (ticks > 5):
            if bike_on:
                hmi.set('sleep',1)
                bike_on = False
                log.close()
                print('Log Closed')
                # print(ticks)
                # Debounce
                ticks = 0
                
                # If light switch is still On, turn off the light anyway
                if headlight_switch.value():
                    light_on = False
                    hmi.light = 0
                    # Off
                    headlight.high()
        
        if bike_on:
            if (horn_switch.value()) and (ticks > 5):
                if not horn_on:
                    horn.low()
                    horn_on = True
                    ticks = 0
                    
            if (not horn_switch.value()) and (ticks > 5):
                if horn_on: 
                    horn_on = False
                    horn.high()
                    ticks = 0
            
            if (headlight_switch.value()) and (ticks > 5):
                # If we enter here, there is a change of state and we
                # must debounce key
                if not light_on: 
                    hmi.light = 1
                    light_on = True
                    # low() means turn On
                    headlight.low()
                    # Debounce
                    ticks = 0

            if (not headlight_switch.value()) and (ticks > 5):
                if light_on:
                    hmi.light = 0
                    # high() means Off
                    headlight.high()
                    light_on = False
                    # Debounce
                    ticks = 0 

    if bike_on:
            # Scheduled by Timer 4
        if (request_kelly_data):
            # read takes 0.3ms
            # wrie takes 1.6ms
            # total of about 2ms 
            
            #print("Request Kelly Data")
            if kelly_3A:
    #                t1 = ut.ticks_us()
                kelly.send_3A()
    #                t2 = ut.ticks_us()
    #                print("Kelly Request", ut.ticks_diff(t2, t1))

            else:
                kelly.send_3B()

            request_kelly_data = False

        elif (read_kelly_data):
            #print("Read Kelly Data")
    #           t1 = ut.ticks_us()
            kelly.get_data()

            if (kelly_3A):
                hmi.update_volts(kelly.volts)
                hmi.update_motor_temp(kelly.motor_temp)
                # hmi.regen = kelly.regen
                # hmi.throttle = kelly.throttle
            else:
                hmi.update_speed(kelly.speed)
                hmi.update_amps(kelly.amps)
                # perhaps the best place to log
                # pack('24s',get_datetime_string())
             
    #            t2 = ut.ticks_us()
    #            print("Kelly Read", ut.ticks_diff(t2, t1))             
                
            kelly_3A = not kelly_3A
            read_kelly_data = False

        # Scheduled by Timer 2
        elif (update_hmi):
            # print("Update HMI")
            # Nothing in update_page() generates a return value
            # So it should be safe to ingore serial data here and
            # look for serial data more often but elsewhere.
            
    #            t1 = ut.ticks_us()     
            hmi.update_page()
    #            t2 = ut.ticks_us()
    #            print("HMI", ut.ticks_diff(t2, t1))
            
            update_hmi = False
        
        # Scheduled by Timer 9
        # Frequncy matches IMU update frequency
        # Each time called there should be data ready
        # and waiting.
        elif (update_imu):
            # 1ms per iteration
    #            t1 = ut.ticks_us()
            ret = imu.read_IMU_data()
    #            t2 = ut.ticks_us()
    #            print("imu", ret, ut.ticks_diff(t2, t1))

            
            update_imu = False
        
        # Scheduled by Timer 7
        elif (update_graph):
            # 3ms per iteration
            if hmi.page == hmi.PAGE_GRAPH:
    #                t1 = ut.ticks_us()                
                hmi.update_graph()
    #                t2 = ut.ticks_us()
    #                print("Graph", ut.ticks_diff(t2, t1))
                     
            update_graph = False
        
        elif (update_log):
            dt = get_datetime_string()
            log_string = dt + ',' + str(kelly.volts) + ',' + str(kelly.amps) + ',' + str(kelly.speed // 16) + ',' + str(kelly.motor_temp - 10) + ',' 
            log_string += str(kelly.throttle) + ',' + str(kelly.regen) + ',' 
            log_string += "{0:.2f}".format(imu.ax) + ',' + "{0:.2f}".format(imu.ay) + ',' + "{0:.2f}".format(imu.az) + ',' 
            log_string += "{0:.2f}".format(imu.angx) + ',' + "{0:.2f}".format(imu.angy) + ',' + "{0:.2f}".format(imu.angz) + '\n' 
            # Having a issue with random not conforming entries
            # Adding an assertion check, temporary work around
            ct1 = log_string.count(',')
            ct2 = log_string.count('\n')
            if (ct1 == 13) and (ct2 == 1) :
                log.write(log_string)            
                # print(log_string)
            
            
            update_log = False
        
        # Every loop look for HMI Return Data
        if (hmi.serial.any()):
            # This is typically button pushes
            # or page changes. 
            hmi.process_return()





