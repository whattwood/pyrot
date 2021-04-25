# Settings for pyrot

# GPIO pins for rotary encoder
enc_az = 26 #this pin is used for the azimuth sensor
enc_el = 24 #this pin will be ussed for elevation sensor in the future

# Relay outputs
relay_board = 0x11 #i2c relay board address
relay_cw = 0x01 #i2c relay number for clockwise direction
relay_ccw = 0x02 #i2c relay number for counterclockwise direction
relay_on = 0x01 #i2c relay on command
relay_off = 0x00 #i2c relay off command
