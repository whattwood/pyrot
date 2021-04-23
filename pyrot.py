#!/usr/bin/env python3
# Pi Rotator controller software by VE6WK 2021

import pigpio
pi = pigpio.pi()

import time

import sys, select, os
os.system('cls' if os.name == 'nt' else 'clear')
os.system("screen -S pyrot1 -dm socat -u -u pty,raw,echo=0,link=/dev/ttyS21 pty,raw,echo=0,link=/dev/ttyS22") #create virtual serial ports on a detached screen
os.system("screen -S pyrot2 -dm rotctld -m 202 -r /dev/ttyS21") #start hamlib on a detached screen

from encoder import Encoder

import settings
relay_bus=pi.i2c_open(1,settings.relay_board)
relay_cw_on=[settings.relay_cw,settings.relay_on]
relay_cw_off=[settings.relay_cw,settings.relay_off]
relay_ccw_on=[settings.relay_ccw,settings.relay_on]
relay_ccw_off=[settings.relay_ccw,settings.relay_off]

def valueChanged(value):
        value=e1.getValue()
        os.system('cls' if os.name == 'nt' else 'clear')
        print("GPIO Clk Pin:",settings.enc_clk,", GPIO Bk Pin:",settings.enc_bk)
        print("Encoder Value:",value)
        print("Press Control-C to exit")

e1 = Encoder(settings.enc_clk, settings.enc_bk, callback=valueChanged) # Run valueChanged when encoder moves

value = e1.getValue()
os.system('cls' if os.name == 'nt' else 'clear')
print("GPIO Clk Pin:",settings.enc_clk,", GPIO Bk Pin:",settings.enc_bk)
print("Encoder Value:",value)
print("Press Control-C to exit")
pi.i2c_write_device(relay_bus,relay_cw_off)
pi.i2c_write_device(relay_bus,relay_ccw_off)

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
                time.sleep(1)
except KeyboardInterrupt:
    pass

print("\r\nFinal Encoder Value:",value)
os.system("screen -S pyrot1 -X quit")
os.system("screen -S pyrot2 -X quit")
pi.i2c_write_device(relay_bus,relay_cw_off)
pi.i2c_write_device(relay_bus,relay_ccw_off)
pi.i2c_close(relay_bus)
print("Cleaned up running processes")
