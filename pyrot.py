#!/usr/bin/env python3
# Pi Rotator controller software by VE6WK 2021

# imports and startup software
import time, io, sys, select, os
os.system("pigpiod") #start pigpio daemon if it hasn't already
import pigpio
pi = pigpio.pi()

import settings
relay_bus=pi.i2c_open(1,settings.relay_board)
relay_cw_on=[settings.relay_cw,settings.relay_on]
relay_cw_off=[settings.relay_cw,settings.relay_off]
relay_ccw_on=[settings.relay_ccw,settings.relay_on]
relay_ccw_off=[settings.relay_ccw,settings.relay_off]

os.system('cls' if os.name == 'nt' else 'clear')
os.system("screen -S pyrot1 -dm socat -u -u pty,raw,echo=0,link=/dev/ttyS21 pty,raw,echo=0,link=/dev/ttyS22") #create virtual serial ports on a detached screen
os.system("screen -S pyrot2 -dm rotctld -m 202 -r /dev/ttyS21") #start hamlib on a detached screen

from encoder import Encoder

# This happens when encoder moves
def valueChanged(value):
    value=e1.getValue()
    os.system('cls' if os.name == 'nt' else 'clear')
    print("GPIO Clk Pin:",settings.enc_clk,", GPIO Bk Pin:",settings.enc_bk)
    print("Encoder Value:",value)
    print("Press Control-C to exit")

# Run valueChanged when encoder moves
e1 = Encoder(settings.enc_clk, settings.enc_bk, callback=valueChanged)

# Initial section of code
value = e1.getValue()
os.system('cls' if os.name == 'nt' else 'clear')
print("GPIO Clk Pin:",settings.enc_clk,", GPIO Bk Pin:",settings.enc_bk)
print("Encoder Value:",value)
print("Press Control-C to exit")
pi.i2c_write_device(relay_bus,relay_cw_off)
pi.i2c_write_device(relay_bus,relay_ccw_off)
tty = io.TextIOWrapper(io.FileIO(os.open("/dev/ttyS22",os.O_NOCTTY | os.O_RDWR),"r+"))

# Loop while code runs
try:
    while value < 5 and value > -5:
            value=e1.getValue()
            if value == settings.heading:
                    pi.i2c_write_device(relay_bus,relay_cw_off)
                    pi.i2c_write_device(relay_bus,relay_ccw_off)
            if value > settings.heading:
                    pi.i2c_write_device(relay_bus,relay_cw_on)
                    pi.i2c_write_device(relay_bus,relay_ccw_off)
            if value < settings.heading:
                    pi.i2c_write_device(relay_bus,relay_ccw_on)
                    pi.i2c_write_device(relay_bus,relay_cw_off)
            for line in iter(tty.readline, None):
                print(line.strip())
                tty.writelines("AZ40.1,0.0 EL0.0,0.0\n")
            time.sleep(1)
except KeyboardInterrupt:
    pass

# Script shutdown commands
print("\r\nFinal Encoder Value:",value)
os.system("screen -S pyrot1 -X quit")
os.system("screen -S pyrot2 -X quit")
pi.i2c_write_device(relay_bus,relay_cw_off)
pi.i2c_write_device(relay_bus,relay_ccw_off)
pi.i2c_close(relay_bus)
print("Cleaned up running processes")
