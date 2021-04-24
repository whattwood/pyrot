# pyrot
Python antenna rotator controller for Raspberry Pi

Requirements:
- hamlib must be installed
- pigpio must be installed
- requires 2 x i2c relays
- reads single pulse 1 degree rotary encoder only (so far...)

2021.04.24 Update
- Now takes commands from rotctl and responds with feedback
- Still requires a way to store known position in a file in case script stops

2021.04.22 Initial version
Still To Do:
1. Write module that takes commands and responds to rotctld requests
2. Add pre-requesites to documentation
3. Draw wiring diagram for Alpha Spid rotator
4. 
