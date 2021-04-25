# pyrot
## Python antenna rotator controller for Raspberry Pi

### Files:
setting.py #Settings for the script, modify to match your hardware
pyrot.py #Rotator control script, this is the one you run
easycom.txt #Reference for easycom commands, not required
encoder.py #Not used, function for reading rotary encoder. May be implemented in the future

### Requirements:
- designed for Python 3
- hamlib must be installed
- pigpio must be installed
- requires 2 x i2c relays
- reads single pulse 1 degree rotary encoder only (so far...)

### Current Functionality
- Tested with AlphaSpid RAK rotator
- Azimuth control only
- Set up for hamlib, but could easily be modified to accept Easycom commands on Raspberry Pi serial port by changin socat line

## Installation Instructions

1. ```cd /usr/src```
2. ```git clone https://github.com/whattwood/pyrot.git```
3. ```cd /pyrot```
4. ```nano setting.py``` Change settings to match your hardware, save with Control-x
5. ```python -V``` Ensure python version is at least 3
6. ```python pyrot.py``` Run pyrot script to ensure it works
7. ```chmod +x pyrot.py``` Make pyrot executable
8. Add /usr/src/pyrot/pyrot.py to startup using /etc/rc.local or cron job



-------------------------------------------------------------------
## CHANGELOG

2021.04.25 Update
- fixed sensor bounce
- store position in file when rotator is stopped for 10 seconds and on script shutdown
- Still requires wiring diagram
- should clean up code to prevent error messages when pigpiod is already running and when rotator position file already exisits

2021.04.24 Update
- ISSUE: need some debounce, not counting GPIO pin clicks correctly
- Now takes commands from rotctl and responds with feedback
- Still requires a way to store known position in a file in case script stops
- Still requires wiring diagram

2021.04.22 Initial version
Still To Do:
- Write module that takes commands and responds to rotctld requests
- Add pre-requesites to documentation
- Draw wiring diagram for Alpha Spid rotator
