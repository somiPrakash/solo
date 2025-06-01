import machine
import utime
import time
from time import sleep

import sys


mid_pin = machine.Pin(28,machine.Pin.IN,machine.Pin.PULL_UP)
right_pin = machine.Pin(27,machine.Pin.IN,machine.Pin.PULL_UP)
left_pin = machine.Pin(26,machine.Pin.IN,machine.Pin.PULL_UP)
down_pin = machine.Pin(21,machine.Pin.IN,machine.Pin.PULL_UP)
up_pin = machine.Pin(22,machine.Pin.IN,machine.Pin.PULL_UP)


while(1):
    if(mid_pin.value() == 0):
        print("Mid")
    elif(right_pin.value() == 0):
        print("Right")
    elif(left_pin.value() == 0):
        print("Left")
    elif(down_pin.value()== 0):
        print("Down")
    elif(up_pin.value() == 0):
        print("Up")
    else:
        print("No button pressed")
    sleep(0.05)

