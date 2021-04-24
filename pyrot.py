#!/usr/bin/env python3
# Pi Rotator controller software by VE6WK 2021 intended for DC rotator with pulse sensor such as Alpha Spid

# imports and startup software
import time, sys, select, os, serial
os.system("pigpiod") #start pigpio daemon if it hasn't already
import pigpio
pi = pigpio.pi()

import settings
relay_bus=pi.i2c_open(1,settings.relay_board)
relay_cw_on=[settings.relay_cw,settings.relay_on]
relay_cw_off=[settings.relay_cw,settings.relay_off]
relay_ccw_on=[settings.relay_ccw,settings.relay_on]
relay_ccw_off=[settings.relay_ccw,settings.relay_off]

os.system('clear')
os.system("screen -S pyrot1 -dm socat pty,raw,echo=0,link=/dev/ttyS21 pty,raw,echo=0,link=/dev/ttyS22") #create virtual serial ports on a detached screen
os.system("screen -S pyrot2 -dm rotctld -m 202 -r /dev/ttyS21") #start hamlib on a detached screen

from encoder import Encoder

# This happens when encoder moves
def valueChanged(relativePosition):
    relativePosition=encoderResult.getValue()
    os.system('clear')
    print("GPIO Clk Pin:",settings.enc_clk,", GPIO Bk Pin:",settings.enc_bk)
    print("Encoder Value:",relativePosition)
    print("Press Control-C to exit")

# Run valueChanged when encoder moves
encoderResult = Encoder(settings.enc_clk, settings.enc_bk, callback=valueChanged)

# Initial section of code, runs once
relativePosition = encoderResult.getValue()
os.system('clear')
print("GPIO Clk Pin:",settings.enc_clk,", GPIO Bk Pin:",settings.enc_bk)
print("Encoder Value:",relativePosition)
print("Press Control-C to exit")
pi.i2c_write_device(relay_bus,relay_cw_off) #turn clockwise relay off
pi.i2c_write_device(relay_bus,relay_ccw_off) #turn counter-clockwise relay off
ser = serial.Serial('/dev/ttyS22', 115200, timeout = 1) #connect to serial port piped to rotctld
readOut = 0
azActual = 180.0
elActual = 0.0
azDesired = azActual
elDesired = elActual
azelReply = "AZ" + str(azActual) + " EL" + str(elActual) # reply to requests frm hamlib
commandedBearing = [0.0, 0.0]

# main code loop
try:
    while True:
        #time.sleep(.1)
        while True:
            readOut = ser.readline().decode('ascii')
            print ("AZ=",azActual,",desire:",azDesired," EL=",elActual,",desire:",elDesired," Command from Hamlib: ", readOut)
            if "AZ EL" in readOut:
                ser.write(str(azelReply).encode('ascii'))
                #print ("AZ EL request reply written: ", azelReply)
            elif "AZ" in readOut:
                newstr = ''.join((ch if ch in '0123456789.-e' else ' ') for ch in readOut)
                commandedBearing = [float(i) for i in newstr.split()]
                #print("Az/El heading found: ",commandedBearing)
            elif "SA SE" in readOut:
                commandedBearing = [azActual, elActual]
                pi.i2c_write_device(relay_bus,relay_cw_off)
                pi.i2c_write_device(relay_bus,relay_ccw_off)
            elif readOut != "":
                print ("UNKNOWN ROTATOR COMMAND:", readOut)
            if commandedBearing[0] != None:
                    azDesired = (commandedBearing[0])
            if commandedBearing[1] != None:
                elDesired = (commandedBearing[1])
                elActual = elDesired
            if azDesired < azActual - 2:
                azActual -= 1
            if azDesired > azActual + 2:
                azActual += 1
            readOut = ""
            azelReply = "AZ" + str(azActual) + " EL" + str(elActual)
            time.sleep(.05)
            break
        ser.flush() #flush the serial buffer

        relativePosition = encoderResult.getValue()
        if relativePosition == settings.heading:
                pi.i2c_write_device(relay_bus,relay_cw_off)
                pi.i2c_write_device(relay_bus,relay_ccw_off)
        if relativePosition > settings.heading:
                pi.i2c_write_device(relay_bus,relay_cw_on)
                pi.i2c_write_device(relay_bus,relay_ccw_off)
        if relativePosition < settings.heading:
                pi.i2c_write_device(relay_bus,relay_ccw_on)
                pi.i2c_write_device(relay_bus,relay_cw_off)
        time.sleep(.05)
except KeyboardInterrupt:
    pass

# Script shutdown commands
print("\r\nFinal Encoder Value:",relativePosition)
os.system("screen -S pyrot1 -X quit")
os.system("screen -S pyrot2 -X quit")
pi.i2c_write_device(relay_bus,relay_cw_off)
pi.i2c_write_device(relay_bus,relay_ccw_off)
pi.i2c_close(relay_bus)
print("Cleaned up running processes")
