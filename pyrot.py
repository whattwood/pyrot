#!/usr/bin/env python3
# Pi Rotator controller software by VE6WK 2021 intended for DC rotator with pulse sensor such as Alpha Spid

import time, sys, select, os, serial #load the python modules we'll be using #imports and startup software

import os.path
from os import path #used for checking whether files exist

tmp = os.popen("ps -Af").read() #detect if pigpiod is already running
processCount = tmp.count('pigpiod')
if processCount > 0:
    print("pigpiod already running...")
else:
    os.system("pigpiod") #start pigpio daemon if it hasn't already

import pigpio
pi = pigpio.pi() #define which Raspberry Pi the pigpio daemon will control - the local one of course!

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD) # choose the pin numbering scheme

import settings #read our settings.py file and set the objects below
relay_bus=pi.i2c_open(1,settings.relay_board)
relay_cw_on=[settings.relay_cw,settings.relay_on]
relay_cw_off=[settings.relay_cw,settings.relay_off]
relay_ccw_on=[settings.relay_ccw,settings.relay_on]
relay_ccw_off=[settings.relay_ccw,settings.relay_off]

os.system("clear") #clear screen
os.system("screen -S pyrot1 -dm socat pty,raw,echo=0,link=/dev/ttyS21 pty,raw,echo=0,link=/dev/ttyS22") #create virtual serial ports on a detached screen
os.system("screen -S pyrot2 -dm rotctld -m 202 -r /dev/ttyS21 -s 115200") #start hamlib on a detached screen

class bcolors: #setup colours to be used while printing text to screen
    DEFAULT = '\x1b[0m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Encoder: #detect and report state changes to rotator position sensor

    def __init__(self, azPin, callback=None):
        self.azPin = azPin
        self.callback = callback
        self.value = 0
        GPIO.setup(self.azPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.azPin, GPIO.BOTH, callback=self.transitionOccurred)

    def transitionOccurred(self, channel):
        newState = GPIO.input(self.azPin)

        if newState != self.value: #only do this if state has changed (debounce)
            self.value = newState
            if self.callback is not None:
                self.callback(self.value)

    def getValue(self):
        return self.value

def valueChanged(encoderValue): # This happens when encoder moves
    global azMotion, azActual, azLastmotion
    encoderValue=encoderResult.getValue()
    if azMotion == "cw" and encoderValue == 1:
        azActual += 1 #if encoder pin reads 1 and direction is cw, 1 degree is added to azimuth value.
    elif azMotion == "ccw" and encoderValue == 1:
        azActual -= 1 #if encoder pin reads 1 and direction is ccw, 1 degree is subtracted from azimuth value.
    elif azMotion == "stopped" and encoderValue == 1:
        print(bcolors.FAIL + "ERROR! Motion detector while rotator should be stopped!" + bcolors.ENDC)
        with open(filenameLog, 'a') as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "ERROR! Motion detector while rotator should be stopped!\n")
        if azLastMotion == "cw" and encoderValue == 1:
            azActual += 1 #if encoder pin reads 1 and direction is cw, 1 degree is added to azimuth value.
        elif azLastMotion == "ccw" and encoderValue == 1:
            azActual -= 1 #if encoder pin reads 1 and direction is ccw, 1 degree is subtracted from azimuth value.
    elif encoderValue == 1:
        print(bcolors.FAIL + "ENCODER ERROR! Motion detected while rotator in unknown motion state!" + bcolors.ENDC)
        with open(filenameLog, 'a') as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "ENCODER ERROR! Motion detected while rotator in unknown motion state!\n")

# Run valueChanged when encoder senses state change
encoderResult = Encoder(settings.enc_az, callback=valueChanged)

# Initial section of code, runs once
os.system('clear')
print("GPIO AZ Encoder Pin:",settings.enc_az)
print("Press Control-C to exit")
pi.i2c_write_device(relay_bus,relay_cw_off) #turn clockwise relay off
pi.i2c_write_device(relay_bus,relay_ccw_off) #turn counter-clockwise relay off
ser = serial.Serial('/dev/ttyS22', 115200, timeout = .01) #connect to serial port piped to rotctld, timeout is important because reading rs232 stalls the whole script

print ("Does /var/spool/pyrot/pyrot_position.txt exist? " + str(path.isfile("/var/spool/pyrot/pyrot_position.txt")))
if path.isfile("/var/spool/pyrot/pyrot_position.txt") is True:
    filename="/var/spool/pyrot/pyrot_position.txt"
    with open(filename, 'r') as f:
        readOut = f.read()    # results in a str object
    newstr = ''.join((ch if ch in '0123456789.-e' else ' ') for ch in readOut) #read digits in command string
    savedPosition = [float(i) for i in newstr.split()] #save numbers in savedPosition object
    try:
        if savedPosition[0] != None:
            azActual = (savedPosition[0])
    except:
        print(bcolors.FAIL + "/var/spool/pyrot/pyrot_position.txt has invalid values!" + bcolors.ENDC)
        exit()
    try:
        if savedPosition[1] != None:
            elActual = (savedPosition[1])
    except:
        print(bcolors.FAIL + "/var/spool/pyrot/pyrot_position.txt has invalid values!" + bcolors.ENDC)
        exit()
else:
    print(bcolors.FAIL + "Previous position file does not exist, setting values to 0 degrees! Ensure rotator position is North or press Control-C NOW!!!" + bcolors.ENDC)
    print("Waiting 20 seconds for input...")
    os.system("mkdir /var/spool/pyrot/")
    os.system("touch /var/spool/pyrot/pyrot_position.txt")
    azActual = 0.0
    elActual = 0.0
    time.sleep(20)

filenameLog = "/var/spool/pyrot/pyrot_log.txt"
print ("Does " + filenameLog + " exist? " + str(path.isfile(filenameLog)))
if path.isfile("filenameLog") is True:
    with open(filenameLog, 'a') as f:
         f.write(time.strftime("%Y-%m-%d %H:%M:%S") + ' pyrot started.\n')
else:
    os.system("touch " + filenameLog)
    with open(filenameLog, 'a') as f:
         f.write(time.strftime("%Y-%m-%d %H:%M:%S") + ' pyrot started.\n')

count = 0
azMotion = "stopped"
azLastMotion = azMotion
azDesired = azActual
elDesired = elActual
azStable = azActual
azStableCount = 0
azelReply = "AZ" + str(azActual) + " EL" + str(elActual) # String for replies to position inquiries from hamlib
commandedBearing = [azActual, elActual]

# main code loop
try:
    while True:
        while True:
            count += 1
            readOut = ser.readline().decode('ascii') #read serial port for any updated commands
            if "AZ EL" in readOut: #if position is requested by hamlib
                ser.write(str(azelReply).encode('ascii')) #reply with position
            elif "AZ" in readOut: #if position command is received
                newstr = ''.join((ch if ch in '0123456789.-e' else ' ') for ch in readOut) #read digits in command string
                commandedBearing = [float(i) for i in newstr.split()] #save numbers in commandedBearing
            elif "SA SE" in readOut: #if stop command is received
                commandedBearing = [azActual, elActual] #set commandedBearing to current positions
                pi.i2c_write_device(relay_bus,relay_cw_off) #turn off relays
                pi.i2c_write_device(relay_bus,relay_ccw_off)
                azLastMotion = azMotion
                azMotion = "stopped"
            elif readOut != "":
                print ("UNKNOWN ROTATOR COMMAND:", readOut)
            if commandedBearing[0] != None:
                    azDesired = (commandedBearing[0])
            if commandedBearing[1] != None:
                elDesired = (commandedBearing[1])
                elActual = elDesired #ignore elevation commands and set imaginary elevation to commanded elevation
            if azDesired < azActual - 1: #if the desired position is different than the actual position by more than 1 degree
                pi.i2c_write_device(relay_bus,relay_ccw_on)
                pi.i2c_write_device(relay_bus,relay_cw_off)
                azMotion = "ccw"
            elif azDesired > azActual + 1: #if the desired position is different than the actual position by more than 1 degree
                pi.i2c_write_device(relay_bus,relay_cw_on)
                pi.i2c_write_device(relay_bus,relay_ccw_off)
                azMotion = "cw"
            elif azMotion != "stopped":
                pi.i2c_write_device(relay_bus,relay_cw_off)
                pi.i2c_write_device(relay_bus,relay_ccw_off)
                azLastMotion = azMotion
                azMotion = "stopped"
            readOut = ""
            azelReply = "AZ" + str(azActual) + " EL" + str(elActual)
            if (count/50).is_integer() is True: #every 5 secods or so
                os.system('clear') #clear screen
                print (bcolors.YELLOW + "AZ=",azActual,", desire:",azDesired," EL=",elActual,", desire:",elDesired, " " + bcolors.ENDC)
            if (count/10).is_integer() is True: #this portion of code saves the rotator position to a file once it's been stopped for 10 seconds or so
                if azStable != azActual:
                    azStable = azActual
                    azStableCount = 0
                elif azStableCount < 12:
                    azStableCount +=1
                if azStableCount == 10:
                    filename='/var/spool/pyrot/pyrot_position.txt'
                    fileString = (str(azActual) + ", " + str(elActual) + "\n")
                    with open(filename, 'w') as filetowrite:
                        filetowrite.write(fileString)
                    print (bcolors.OKGREEN + "Saving AZ/EL positions to file " + bcolors.ENDC)
            if count > 1000: #at approx 100 seconds, reset count
                count = 0
            time.sleep(.01) #slow script down just in case it runs away
            break
        ser.flush() #flush the serial buffer
        time.sleep(.01)
except KeyboardInterrupt:
    pass

# Script shutdown commands
print("Final Azimuth Value:",azActual)
print("Final Elevation Value:",elActual)
os.system("screen -S pyrot1 -X quit")
os.system("screen -S pyrot2 -X quit")
pi.i2c_write_device(relay_bus,relay_cw_off)
pi.i2c_write_device(relay_bus,relay_ccw_off)
pi.i2c_close(relay_bus)
print(bcolors.DEFAULT + "Cleaned up running processes")
filename='/var/spool/pyrot/pyrot_position.txt'
fileString = (str(azActual) + ", " + str(elActual) + "\n")
with open(filename, 'w') as filetowrite:
    filetowrite.write(fileString)
print (bcolors.OKGREEN + "Saved final AZ/EL positions to file " + bcolors.ENDC)
with open(filenameLog, 'a') as f:
     f.write(time.strftime("%Y-%m-%d %H:%M:%S") + ' pyrot stopped.\n')
