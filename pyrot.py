#!/usr/bin/env python3
# Pi Rotator controller software by VE6WK 2021 intended for DC rotator with pulse sensor such as Alpha Spid

# imports and startup software
import time, sys, select, os, serial #load the python modules we'll be using
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

os.system('clear') #clear screen
os.system("screen -S pyrot1 -dm socat pty,raw,echo=0,link=/dev/ttyS21 pty,raw,echo=0,link=/dev/ttyS22") #create virtual serial ports on a detached screen
os.system("screen -S pyrot2 -dm rotctld -m 202 -r /dev/ttyS21") #start hamlib on a detached screen

class Encoder:

    def __init__(self, leftPin, callback=None):
        self.leftPin = leftPin
        self.callback = callback
        self.value = 0
        GPIO.setup(self.leftPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.leftPin, GPIO.BOTH, callback=self.transitionOccurred)

    def transitionOccurred(self, channel):
        p1 = GPIO.input(self.leftPin)
        p2 = 0
        newState = "{}{}".format(p1, p2)

        if newState == "10": # if pin high
            self.value = 1
            if self.callback is not None:
                self.callback(self.value)

        if newState == "00": # if pin low
            self.value = 0
            if self.callback is not None:
                self.callback(self.value)
        print("newState value: ",newState,"    self.value: ",self.value)

    def getValue(self):
        return self.value

# This happens when encoder moves
def valueChanged(encoderValue):
    global azMotion, azActual, azLastmotion
    encoderValue=encoderResult.getValue()
    #os.system('clear')
    print("Encoder New Value:",encoderValue)
    print("Press Control-C to exit")
    if azMotion == "cw" and encoderValue == 1:
        azActual += 1 #if encoder pin reads 1 and direction is cw, 1 degree is added to azimuth value.
    elif azMotion == "ccw" and encoderValue == 1:
        azActual -= 1 #if encoder pin reads 1 and direction is ccw, 1 degree is subtracted from azimuth value.
    elif azMotion == "stopped" and encoderValue == 1:
        print("ERROR! Motion detector while rotator should be stopped!")
        if azLastMotion == "cw" and encoderValue == 1:
            azActual += 1 #if encoder pin reads 1 and direction is cw, 1 degree is added to azimuth value.
        elif azLastMotion == "ccw" and encoderValue == 1:
            azActual -= 1 #if encoder pin reads 1 and direction is ccw, 1 degree is subtracted from azimuth value.
    elif encoderValue == 1:
        print("ENCODER ERROR! Motion detected while rotator in unknown motion state!")

# Run valueChanged when encoder senses state change
encoderResult = Encoder(settings.enc_clk, callback=valueChanged)

# Initial section of code, runs once
os.system('clear')
print("GPIO Clk Pin:",settings.enc_clk)
print("Press Control-C to exit")
pi.i2c_write_device(relay_bus,relay_cw_off) #turn clockwise relay off
pi.i2c_write_device(relay_bus,relay_ccw_off) #turn counter-clockwise relay off
ser = serial.Serial('/dev/ttyS22', 115200, timeout = 1) #connect to serial port piped to rotctld
readOut = 0
azBegin = 0.0
azMotion = "stopped"
azLastMotion = azMotion
azActual = azBegin
elActual = 0.0
azDesired = azActual
elDesired = elActual
azelReply = "AZ" + str(azActual) + " EL" + str(elActual) # String for replies to position inquiries from hamlib
commandedBearing = [0.0, 0.0]

# main code loop
try:
    while True:
        #time.sleep(.1)
        while True:
            readOut = ser.readline().decode('ascii') #read serial port for any updated commands
            print ("AZ=",azActual,",desire:",azDesired," EL=",elActual,",desire:",elDesired," Command from Hamlib: ", readOut)
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
            if azDesired < azActual - 2:
                pi.i2c_write_device(relay_bus,relay_ccw_on)
                pi.i2c_write_device(relay_bus,relay_cw_off)
                azMotion = "ccw"
            elif azDesired > azActual + 2:
                pi.i2c_write_device(relay_bus,relay_cw_on)
                pi.i2c_write_device(relay_bus,relay_ccw_off)
                azMotion = "cw"
            else:
                pi.i2c_write_device(relay_bus,relay_cw_off)
                pi.i2c_write_device(relay_bus,relay_ccw_off)
            readOut = ""
            azelReply = "AZ" + str(azActual) + " EL" + str(elActual)
            time.sleep(.01)
            break
        ser.flush() #flush the serial buffer
        time.sleep(.01)
except KeyboardInterrupt:
    pass

# Script shutdown commands
print("\r\nFinal Azimuth Value:",azActual)
os.system("screen -S pyrot1 -X quit")
os.system("screen -S pyrot2 -X quit")
pi.i2c_write_device(relay_bus,relay_cw_off)
pi.i2c_write_device(relay_bus,relay_ccw_off)
pi.i2c_close(relay_bus)
print("Cleaned up running processes")
