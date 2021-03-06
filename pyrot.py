#!/usr/bin/env python3
# Pi Rotator controller software by VE6WK 2021 intended for DC rotator with pulse sensor such as Alpha Spid

import time, sys, select, os, serial, configparser #load the python modules we'll be using #imports and startup software

import os.path
from os import path #used for checking whether files econfigparserxist

os.system("clear") #clear screen
time.sleep(.1)

print("\n    pyrot is a Python Rotator controller typically used by Ham Radio Operators")
#print("\n    This program is free software: you can redistribute it and/or modify\n    it under the terms of the GNU General Public License as published by\n    the Free Software Foundation, either version 3 of the License, or\n    any later version.")
#print("\n    This program is distributed in the hope that it will be useful,\n    but WITHOUT ANY WARRANTY; without even the implied warranty of\n    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n    GNU General Public License for more details.")
print("\n\n   pyrot  Copyright (C) 2021 by VE6WK")
print("\n\n    This program comes with ABSOLUTELY NO WARRANTY.\n    This is free software, and you are welcome to redistribute it\n    under certain conditions.\n\n")

tmp = os.popen("ps -Af").read() #detect if pigpiod is already running
processCount = tmp.count('pigpiod')
if processCount > 0:
    print("pigpiod already running...")
else:
    os.system("pigpiod") #start pigpio daemon if it hasn't already
    time.sleep(.3)

import pigpio
pi = pigpio.pi() #define which Raspberry Pi the pigpio daemon will control - the local one of course!

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD) #choose the pin numbering scheme

#import settings from our settings.txt file and set the i2c objects below
config = configparser.ConfigParser()
config.read("/etc/pyrot/settings.txt")
relay_bus=pi.i2c_open(1,int(config.get("pyrotvars","relay_board"),16))
relay_cw_on=[int(config.get("pyrotvars","relay_cw"),16),int(config.get("pyrotvars","relay_on"),16)]
relay_cw_off=[int(config.get("pyrotvars","relay_cw"),16),int(config.get("pyrotvars","relay_off"),16)]
relay_ccw_on=[int(config.get("pyrotvars","relay_ccw"),16),int(config.get("pyrotvars","relay_on"),16)]
relay_ccw_off=[int(config.get("pyrotvars","relay_ccw"),16),int(config.get("pyrotvars","relay_off"),16)]
travelspeed=float(config.get("pyrotvars", "travelspeed"))
travelspeedperdegree=round(travelspeed/180,4)
enc_az=int(config.get("pyrotvars", "enc_az"))
comtype=str(config.get("pyrotvars", "comtype"))

os.system("screen -dmS pyrot1 socat pty,raw,echo=0,link=/dev/ttyS21 pty,raw,echo=0,link=/dev/ttyS22") #create virtual serial ports on a detached screen
print("\n   Started socat")
time.sleep(.3)
if comtype == "hamlib":
    os.system("screen -dmS pyrot2 /usr/local/bin/rotctld -m 601 -r /dev/ttyS21 -s 115200") #start hamlib on a detached screen
    print("\n   Started rotctld")
    time.sleep(.3)
elif comtype == "ser2net":
    os.system("screen -dmS pyrot2 /usr/sbin/ser2net -n -c /etc/pyrot/ser2net.conf") #start ser2net using config at /etc/ser2net.conf
    print("\n   Started ser2net")
    time.sleep(.3)

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

def valueChanged(encoderValue): #This happens when encoder moves
    global azMotion, azActual, azLastmotion
    encoderValue=encoderResult.getValue()
    if azMotion == "cw" and encoderValue == 1:
        azActual += 1 #if encoder pin reads 1 and direction is cw, 1 degree is added to azimuth value.
        print(bcolors.OKCYAN + "Movement: + 1 degree" + bcolors.ENDC)
    elif azMotion == "ccw" and encoderValue == 1:
        azActual -= 1 #if encoder pin reads 1 and direction is ccw, 1 degree is subtracted from azimuth value.
        print(bcolors.OKCYAN + "Movement: - 1 degree" + bcolors.ENDC)
    elif azMotion == "stopped" and encoderValue == 1:
        print(bcolors.FAIL + "ERROR! Motion detector while rotator should be stopped!" + bcolors.ENDC)
        with open(filenameLog, 'a') as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " Motion detected while rotator stopped. If you see more than 1 of these messages in a row we have a problem!!\n")
        if azLastMotion == "cw" and encoderValue == 1:
            azActual += 1 #if encoder pin reads 1 and direction is cw, 1 degree is added to azimuth value.
        elif azLastMotion == "ccw" and encoderValue == 1:
            azActual -= 1 #if encoder pin reads 1 and direction is ccw, 1 degree is subtracted from azimuth value.
    elif encoderValue == 1:
        print(bcolors.FAIL + "ENCODER ERROR! Motion detected while rotator in unknown motion state!" + bcolors.ENDC)
        with open(filenameLog, 'a') as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " ENCODER ERROR! Motion detected while rotator in unknown motion state!\n")

# Run valueChanged when encoder senses state change
encoderResult = Encoder(enc_az, callback=valueChanged)

def pyrotShutdown(): #Script shutdown commands
    pi.i2c_write_device(relay_bus,relay_cw_off)
    pi.i2c_write_device(relay_bus,relay_ccw_off)
    pi.i2c_close(relay_bus)
    print("Final Azimuth Value:",azActual)
    print("Final Elevation Value:",elActual)
    os.system("screen -S pyrot1 -X quit")
    os.system("screen -S pyrot2 -X quit")
    os.system("kill $(ps aux | grep '/etc/pyrot/ser2net.conf' | awk '{print $2}')")
    print(bcolors.DEFAULT + "Cleaned up running processes")
    filename='/var/spool/pyrot/pyrot_position.txt'
    fileString = (str(azActual) + ", " + str(elActual) + "\n")
    with open(filename, 'w') as filetowrite:
        filetowrite.write(fileString)
    print (bcolors.OKGREEN + "Saved final AZ/EL positions to file " + bcolors.ENDC)
    with open(filenameLog, 'a') as f:
         f.write(time.strftime("%Y-%m-%d %H:%M:%S") + ' pyrot stopped at AZ/EL: ' + str(azActual) + ', ' + str(elActual) + '\n')
    exit()


# Initial section of code, runs once
os.system('clear')
print("GPIO AZ Encoder Pin:",config.get("pyrotvars", "enc_az"))
print("Press Control-C to exit")
pi.i2c_write_device(relay_bus,relay_cw_off) #turn clockwise relay off
pi.i2c_write_device(relay_bus,relay_ccw_off) #turn counter-clockwise relay off
ser = serial.Serial('/dev/ttyS22', 115200, timeout = .01) #connect to serial port piped to rotctld, timeout is important because reading rs232 stalls the whole script

print ("Does /var/spool/pyrot/pyrot_position.txt exist? " + str(path.isfile("/var/spool/pyrot/pyrot_position.txt")))
if path.isfile("/var/spool/pyrot/pyrot_position.txt") is True:
    filename="/var/spool/pyrot/pyrot_position.txt"
    with open(filename, 'r') as f:
        readOut = f.read()    # results in a str object
    print(readOut)
    newstr = ''.join((ch if ch in '0123456789.-e' else ' ') for ch in readOut) #read digits in command string
    savedPosition = [int(i) for i in newstr.split()] #save numbers in savedPosition object
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
    print(bcolors.FAIL + "Previous position file does not exist, setting values to 0 degrees! Ensure rotator position is South or press Control-C NOW!!!" + bcolors.ENDC)
    print("Waiting 20 seconds for input...")
    os.system("mkdir /var/spool/pyrot/")
    os.system("touch /var/spool/pyrot/pyrot_position.txt")
    azActual = 180
    elActual = 000
    time.sleep(20)

filenameLog = "/var/spool/pyrot/pyrot_log.txt"
print ("Does " + filenameLog + " exist? " + str(path.isfile(filenameLog)))
if path.isfile("filenameLog") is True:
    with open(filenameLog, 'a') as f:
         f.write(time.strftime("%Y-%m-%d %H:%M:%S") + ' pyrot started with AZ/EL: ' + str(azActual) + ', ' + str(elActual) + '\n')
else:
    os.system("touch " + filenameLog)
    with open(filenameLog, 'a') as f:
         f.write(time.strftime("%Y-%m-%d %H:%M:%S") + ' pyrot started with AZ/EL: ' + str(azActual) + ', ' + str(elActual) + '\n')

count = 0
azMotion = "stopped"
azLastMotion = azMotion
azDesired = azActual
elDesired = elActual
azStable = azActual
azStableCount = 0
commandedBearing = [azActual, elActual]
readBytes = ""
readTemp = ""
readOut = ""
readTimer = 0

# main code loop
try:
    while True:
        while True:
            count += 1
            readBytes += ser.read(size=16).decode('ascii') #read serial port for any incoming data
            ser.flushInput()
            if readBytes != "":
                readTimer += 1
                readTemp += readBytes
                readBytes = ""
            elif readTimer > 0: #if 1 cycle goes by and nothing is added to readBytes we assume the incoming data is complete
                readOut = readTemp
                readTemp = ""
                readTimer = 0
            if readOut != "":
                print(bcolors.OKBLUE + "RS-232 Received: " + readOut)
            if "C2" in readOut: #if az el position is requested 
                ser.write(str("+0" + str(azActual).zfill(3) + "+0" + str(elActual).zfill(3) + "\l\n").encode('ascii')) #reply with position, zfill adds leading zeros
                print(bcolors.OKCYAN + "RS-232 Sent: " + "+0" + str(azActual).zfill(3) + "+0" + str(elActual).zfill(3))
            elif "C" in readOut: #if az only position is requested 
                ser.write(str("+0" + str(azActual).zfill(3) + "\l\n").encode('ascii')) #reply with position, zfill adds leading zeros
                print(bcolors.OKCYAN + "RS-232 Sent: " + "+0" + str(azActual).zfill(3))
            elif "B" in readOut: #if az only position is requested
                ser.write(str("+0" + str(elActual).zfill(3) + "\l\n").encode('ascii')) #reply with position, zfill adds leading zeros
                print(bcolors.OKCYAN + "RS-232 Sent: " + "+0" + str(elActual).zfill(3))
            elif "M" in readOut: #if az position command is received
                newstr = ''.join((ch if ch in '0123456789.-e' else ' ') for ch in readOut) #read digits in command string
                azDesired == newstr #save digits  in azDesired
            elif "W" in readOut: #if az/el position command is received
                newstr = ''.join((ch if ch in '0123456789.-e' else ' ') for ch in readOut) #read digits in command string
                commandedBearing = [int(i) for i in newstr.split()] #save numbers in commandedBearing
            elif "S" in readOut: #if all stop command is received
                commandedBearing = [azActual, elActual] #set commandedBearing to current positions
                pi.i2c_write_device(relay_bus,relay_cw_off) #turn off relays
                pi.i2c_write_device(relay_bus,relay_ccw_off)
                azLastMotion = azMotion
                azMotion = "stopped"
            elif "A" in readOut: #if az stop command is received
                commandedBearing = [azActual, elActual] #set commandedBearing to current positions
                pi.i2c_write_device(relay_bus,relay_cw_off) #turn off relays
                pi.i2c_write_device(relay_bus,relay_ccw_off)
                azLastMotion = azMotion
                azMotion = "stopped"
            elif "E" in readOut: #if el stop command is received
                commandedBearing = [azActual, elActual] #set commandedBearing to current positions
                pi.i2c_write_device(relay_bus,relay_cw_off) #turn off relays
                pi.i2c_write_device(relay_bus,relay_ccw_off)
                azLastMotion = azMotion
                azMotion = "stopped"

            elif readOut != "":
                print ("UNKNOWN ROTATOR COMMAND:", readOut)
                with open(filenameLog, 'a') as f:
                    f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " Unknown rotator command received: " + readOut + ".\n")

            if len(commandedBearing) > 0 and commandedBearing[0] != None:
                azDesired = (commandedBearing[0])
            if len(commandedBearing) > 1 and commandedBearing[1] != None:
                elDesired = (commandedBearing[1])
                elActual = elDesired #ignore elevation commands and set imaginary elevation to commanded elevation

            if azDesired > 359: #limit az to predefined stop points
                azDesired = 359
            elif azDesired < 1:
                azDesired = 1

            if elDesired > 89: #limit el to predefined stop points
                elDesired = 89
            elif elDesired < 1:
                elDesired = 1

            if azDesired < azActual - 1 and azMotion != "ccw": #if the desired position is different than the actual position by more than 1 degree
                pi.i2c_write_device(relay_bus,relay_cw_off)
                time.sleep(.3) #pause for a moment so we don't end up going from cw to ccw instantly and blow a fuse
                pi.i2c_write_device(relay_bus,relay_ccw_on)
                azMotionStartTime = time.time()
                azMotionStartPosition = azActual
                azMotion = "ccw"
                azStableCount = 0
            elif azDesired < azActual - 1 and azMotion == "ccw":
                pass
            elif azDesired > azActual + 1 and azMotion != "cw": #if the desired position is different than the actual position by more than 1 degree
                pi.i2c_write_device(relay_bus,relay_ccw_off)
                time.sleep(.3) #pause for a moment so we don't end up going from ccw to cw instantly and blow a fuse
                pi.i2c_write_device(relay_bus,relay_cw_on)
                azMotionStartTime = time.time()
                azMotionStartPosition = azActual
                azMotion = "cw"
                azStableCount = 0
            elif azDesired > azActual - 1 and azMotion == "cw":
                pass
            elif azMotion != "stopped":
                pi.i2c_write_device(relay_bus,relay_cw_off)
                pi.i2c_write_device(relay_bus,relay_ccw_off)
                azLastMotion = azMotion
                azMotionStopTime = time.time()
                azMotionRunTime = azMotionStopTime - azMotionStartTime
                if azMotion=="cw":
                    azMotionExpectedPosition = azMotionStartPosition + int((azMotionRunTime / travelspeedperdegree) + (travelspeedperdegree * .75))
                elif azMotion=="ccw":
                    azMotionExpectedPosition = azMotionStartPosition - int((azMotionRunTime / travelspeedperdegree) + (travelspeedperdegree * .75))
                if azMotionRunTime > .25: #if rotator moved for more than .25 seconds write predicted position to logfile
                    with open(filenameLog, 'a') as f:
                        f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " Direction: " + azMotion + ". Predicted AZ position vs. actual was: " + str(azMotionExpectedPosition) +  " vs. " + str(azActual) + " in " + str(azMotionRunTime) + " seconds.\n")
                azMotion = "stopped"

            readOut = ""
            #azelReply = "AZ" + str(azActual) + " EL" + str(elActual)

            if (count/50).is_integer() is True: #every 5 secods or so
                os.system('clear') #clear screen
                print (bcolors.YELLOW + "AZ=",azActual,", desire:",azDesired," EL=",elActual,", desire:",elDesired, " Rotator speed is: " + str(travelspeedperdegree) + " seconds per degree" + bcolors.ENDC)
            if (count/10).is_integer() is True: #this portion of code saves the rotator position to a file once it's been stopped for 10 seconds or so
                if azStable != azActual:
                    azStable = azActual
                    azStableCount = 0
                elif azStableCount < 12:
                    azStableCount +=1
                if azMotion != "stopped" and azStableCount > 2: #if no motion detected for 3 cycles while rotator should be moving
                    print(bcolors.FAIL + "ERROR! No motion detected while rotator should be turning! Shutting script down." + bcolors.ENDC)
                    azMotionStopTime = time.time()
                    azMotionRunTime = azMotionStopTime - azMotionStartTime
                    if azMotion=="cw":
                        azMotionExpectedPosition = azMotionStartPosition + int((azMotionRunTime / travelspeedperdegree) + (travelspeedperdegree * .75))
                    elif azMotion=="ccw":
                        azMotionExpectedPosition = azMotionStartPosition - int((azMotionRunTime / travelspeedperdegree) + (travelspeedperdegree * .75))
                    with open(filenameLog, 'a') as f:
                        f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " ERROR! No motion detected while rotator should be turning! Shutting script down.\n")
                        f.write("Direction was " + azMotion + " and expected AZ position was: " + str(azMotionExpectedPosition) + "\n")
                    pyrotShutdown() #shut script down
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

        time.sleep(.01)

except KeyboardInterrupt:
    pass


pyrotShutdown() #shut script down
