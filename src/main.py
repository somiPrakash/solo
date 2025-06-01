"""
Exercise on Raspberry Pi Pico/MicroPython
with 320x240 ILI9341 SPI Display
"""

from src.sensors.magnetometer.HMC5883L import HMC5883L
from src.display.ili934xnew import ILI9341, color565
from src.display import glcdfont
from src.display.xpt2046 import Touch

from src.gps.get_gps_data import get_nmea_data
from src.storage import sdcardlib
from src.core.gps_to_pixel import draw_gps_track,get_points_from_osm_file
from src.sensors.barometer.BME280 import BME280
from src.radio.lora.reyax import RYLR998

# I2C Scanner MicroPython
from machine import Pin, SoftI2C,I2C,idle,SPI
from micropython import const
import machine
import os
import time
from time import sleep
import math
import _thread
import json

import network
import requests
from time import sleep
import time
import ntptime


machine.freq(125_000_000)

# Confirm the frequency
print("CPU Frequency:", machine.freq())


GPS_DATA = {}
GPS_SATELLITE_POSITIONING_FIXED_KEYWORD = "A"
GPS_TRACK_FILE_PATH = "/sd/track.json"


# Display properties
SCR_WIDTH = const(320)
SCR_HEIGHT = const(240)
SCR_ROT = const(2)
CENTER_Y = int(SCR_WIDTH/2)
CENTER_X = int(SCR_HEIGHT/2)
LINE_LENGTH = 50
COMPASS_ORIENTATION_CORRECTION = 180

print(os.uname())

# SPI0 pin configurations
TFT_CLK_PIN = const(10)
TFT_MOSI_PIN = const(11)
TFT_MISO_PIN = const(12)

TFT_CS_PIN = const(15)
TFT_RST_PIN = const(14)
TFT_DC_PIN = const(13)


LORA_RX_NODE_ADDRESS = 0  # 0 = All addresses from 0 ~ 65535

display_spi = SPI(
    1,
    baudrate=62000000,
    miso=Pin(TFT_MISO_PIN),
    mosi=Pin(TFT_MOSI_PIN),
    sck=Pin(TFT_CLK_PIN))

gps_serial = machine.UART(0, baudrate=9600, tx=machine.Pin(0), rx=machine.Pin(1))

softI2C1 = machine.SoftI2C(scl=machine.Pin(3), sda=machine.Pin(2), freq=15000)
# softI2C1 = I2C(id=1, scl=Pin(3), sda=Pin(2), freq=10000)
# hmc5883l = HMC5883L(3,2)
hmc5883l = HMC5883L(softI2C1)


display = ILI9341(
    display_spi,
    cs=Pin(TFT_CS_PIN),
    dc=Pin(TFT_DC_PIN),
    rst=Pin(TFT_RST_PIN),
    w=SCR_WIDTH,
    h=SCR_HEIGHT,
    r=SCR_ROT)


sd = None
touch = None
SD_CARD_HARDWARE_ON = True
TOUCHSCREEN_HARDWARE_ON = True
DATA_TO_BE_SENT_ON_LORA = ""
USER_EDIT_TEXT_SCREEN_X_CURSOR_POS = 0
USER_EDIT_TEXT_SCREEN_Y_CURSOR_POS = 0
CHARACTER_WIDTH_IN_PIXELS = 6
CHARACTER_HEIGHT_IN_PIXELS = 8

rows = [
    list("QWERTYUIOP"),        # Row 1 (10 keys)
    list("ASDFGHJKL!<"),        # Row 2 (11 keys)
    list("ZXCVBNM,.?>"),        # Row 3 (11 keys)
    list("0123456789"),        # Row 4 (10 keys, digits unchanged)
    list(" "),        # Row 4 (10 keys, digits unchanged)
]


def get_key_at(x, y):

    display_width = 240
    keyboard_height = 160
    row_height = keyboard_height // len(rows)  # 40
    start_y_offset = 320 - keyboard_height     # 160

    # Check if y is inside the keyboard area
    if y < start_y_offset or y >= 320:
        return None  # Outside keyboard

    row_index = (y - start_y_offset) // row_height
    if row_index >= len(rows):
        return None  # Safety check

    row = rows[row_index]
    num_keys = len(row)
    box_width = display_width // num_keys

    col_index = x // box_width
    if col_index >= num_keys:
        return None  # Outside key area

    return row[col_index]



def touchscreen_press(x, y):
    global DATA_TO_BE_SENT_ON_LORA
    global USER_EDIT_TEXT_SCREEN_X_CURSOR_POS
    global USER_EDIT_TEXT_SCREEN_Y_CURSOR_POS
    
    """Process touchscreen press events."""
    # Y needs to be flipped
    # y = (display.height - 1) - y
    x = (display.width - 1) - x
    
    key_pressed = get_key_at(x, y)
    USER_EDIT_TEXT_SCREEN_X_CURSOR_POS += CHARACTER_WIDTH_IN_PIXELS
    if(USER_EDIT_TEXT_SCREEN_X_CURSOR_POS >= display.width):
        USER_EDIT_TEXT_SCREEN_X_CURSOR_POS = 0
        USER_EDIT_TEXT_SCREEN_Y_CURSOR_POS += CHARACTER_HEIGHT_IN_PIXELS
    display.set_pos(USER_EDIT_TEXT_SCREEN_X_CURSOR_POS ,USER_EDIT_TEXT_SCREEN_Y_CURSOR_POS)
    
    if(key_pressed == ">"):
        _send_ping_data_via_lora(LORA_RX_NODE_ADDRESS,DATA_TO_BE_SENT_ON_LORA)
        DATA_TO_BE_SENT_ON_LORA = ""
    display.print(str(key_pressed))
    DATA_TO_BE_SENT_ON_LORA += str(key_pressed)
    

    # display.print("Screen touched at : {} {}".format(x,y))

if(SD_CARD_HARDWARE_ON):
    # Initialize the SD card
    sdcard_spi = machine.SPI(0,
                    baudrate=2000000,
                    polarity=1,
                    phase=1,
                    bits=8,
                    firstbit=machine.SPI.MSB,
                    sck=machine.Pin(18),
                    mosi=machine.Pin(19),
                    miso=machine.Pin(16))

    sd=sdcardlib.SDCard(sdcard_spi,machine.Pin(20))


if(TOUCHSCREEN_HARDWARE_ON):

    # Initialize the SD card
    touch_spi = machine.SPI(0,
                    baudrate=1000000,
                    sck=machine.Pin(18),
                    mosi=machine.Pin(19),
                    miso=machine.Pin(16))
    
    touch = Touch(touch_spi, cs=Pin(6), int_pin=Pin(7),
                           int_handler=touchscreen_press)
    
    print("Initialized touch : {}".format(touch))

lora_uart1 = machine.UART(1, baudrate=115200, tx=machine.Pin(4), rx=machine.Pin(5))

    
mid_pin = machine.Pin(28,machine.Pin.IN,machine.Pin.PULL_UP)
right_pin = machine.Pin(27,machine.Pin.IN,machine.Pin.PULL_UP)
left_pin = machine.Pin(26,machine.Pin.IN,machine.Pin.PULL_UP)
down_pin = machine.Pin(21,machine.Pin.IN,machine.Pin.PULL_UP)
up_pin = machine.Pin(22,machine.Pin.IN,machine.Pin.PULL_UP)

print(display_spi)
print(gps_serial)
print(softI2C1)
# print(bme280)



def draw_circle(xpos0, ypos0, rad, col=color565(255, 255, 255)):
    x = rad - 1
    y = 0
    dx = 1
    dy = 1
    err = dx - (rad << 1)
    while x >= y:
        display.pixel(xpos0 + x, ypos0 + y, col)
        display.pixel(xpos0 + y, ypos0 + x, col)
        display.pixel(xpos0 - y, ypos0 + x, col)
        display.pixel(xpos0 - x, ypos0 + y, col)
        display.pixel(xpos0 - x, ypos0 - y, col)
        display.pixel(xpos0 - y, ypos0 - x, col)
        display.pixel(xpos0 + y, ypos0 - x, col)
        display.pixel(xpos0 + x, ypos0 - y, col)
        if err <= 0:
            y += 1
            err += dy
            dy += 2
        if err > 0:
            x -= 1
            dx += 2
            err += dx - (rad << 1)
            
# Bresenham’s Line Algorithm         
def draw_line(x0, y0, x1, y1, col=color565(255, 255, 0)):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0

    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1

    if dx > dy:
        err = dx / 2.0
        while x != x1:
            display.pixel(x, y, col)
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            display.pixel(x, y, col)
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    display.pixel(x, y, col)  # Draw final pixel



def draw_heading_line(heading_degrees,color):
    # Convert degrees to radians
    angle_rad = math.radians(heading_degrees)

    # Calculate endpoint of the line
    x2 = int(CENTER_X + LINE_LENGTH * math.cos(angle_rad))
    y2 = int(CENTER_Y - LINE_LENGTH * math.sin(angle_rad))  # y-axis is inverted in display coords

    # Draw the rotating line
    draw_line(CENTER_X, CENTER_Y, x2, y2, col=color)
    
    return x2,y2
    
    
def detect_switch_pressed():
    BUTTON_PRESS_WAIT_TIME = 0.05
    if(mid_pin.value() == 0):
        sleep(BUTTON_PRESS_WAIT_TIME)
        return "M"
    elif(right_pin.value() == 0):
        sleep(BUTTON_PRESS_WAIT_TIME)
        return "R"
    elif(left_pin.value() == 0):
        sleep(BUTTON_PRESS_WAIT_TIME)
        return "L"
    elif(down_pin.value()== 0):
        sleep(BUTTON_PRESS_WAIT_TIME)
        return "D"
    elif(up_pin.value() == 0):
        sleep(BUTTON_PRESS_WAIT_TIME)
        return "U"
    else:
        sleep(BUTTON_PRESS_WAIT_TIME)
        return "N"
        
    
def _draw_tab(x, y, width=240, height=12):
    for i in range(width):
        for j in range(height):
            display.pixel(x + i, y + j, color565(0, 255, 0))

    

def _setup_compass_polygon():
    
#     display.erase()
#     display.set_pos(0,0)
#     display.set_font(tt14)
#     display.set_color(color565(0, 255, 0), color565(0, 0, 0))

    draw_circle(CENTER_X, CENTER_Y,LINE_LENGTH + 8, color565(0, 255, 0))
    draw_circle(CENTER_X, CENTER_Y,LINE_LENGTH + 9, color565(0, 255, 0))
    draw_circle(CENTER_X, CENTER_Y,LINE_LENGTH + 10, color565(0, 255, 0))

    # Calibrate magnetic compass and show true North on screen
    display.set_pos(60 ,158)
    display.print(str("N"))
    display.set_pos(0 ,0)
    

def _draw_compass_heading_line():

    x, y, z = hmc5883l.read()
    
    degrees, minutes = hmc5883l.heading(x,y)
    

    
    # Create the compass line
    x2,y2 = draw_heading_line(degrees + COMPASS_ORIENTATION_CORRECTION,color565(255, 255, 255))
    
    # Erase the compass line 
    draw_heading_line(degrees + COMPASS_ORIENTATION_CORRECTION ,color565(0, 0, 0))
    
    display.print("{} {} {}".format(str(degrees), str(x2) , str(y2)))
    
    
def _get_magnetic_heading_in_degrees():
    x, y, z = hmc5883l.read()
    degrees, minutes = hmc5883l.heading(x,y)
    return degrees
    
def _draw_track_from_gps_coordinates(gps_data):
    utc_time = gps_data["utc_time"]
    latitude = gps_data["raw_latitude"]
    longitude = gps_data["raw_longitude"]
    latitude_direction = gps_data["raw_lat_dir"]
    longitude_direction = gps_data["raw_lon_dir"]
    

def _initialize_sd_card():
    # Create a instance of MicroPython Unix-like Virtual File System (VFS),
    vfs=os.VfsFat(sd)
     
    # Mount the SD card
    os.mount(sd,'/sd')
    
    # Debug print SD card directory and files
    print(os.listdir('/sd'))
    
def _save_gps_data_to_flash():
    
    display.print("Trying to fetch GPS data with Satellite fix .. ")
    gps_data = get_nmea_data(gps_serial)
    while(gps_data == None):
        gps_data = get_nmea_data(gps_serial)
        pass    
    # Write data
    if("satellite_positioning_status" in gps_data.keys()):
        if(gps_data["satellite_positioning_status"] == GPS_SATELLITE_POSITIONING_FIXED_KEYWORD):
            
            magnetic_heading_in_degrees = _get_magnetic_heading_in_degrees()
            gps_data["magnetic_heading_in_degrees"] = magnetic_heading_in_degrees
            display.print("Got Fix data . Saving GPS data to flash ")
            with open(GPS_TRACK_FILE_PATH, "a") as file:
                file.write(json.dumps(gps_data) + "\n")  # Add newline after each JSON entry
                
def _clear_track_file():
    display.print("INFO - Clearing track file")
    with open(GPS_TRACK_FILE_PATH, "w") as file:
        pass

def _draw_gps_track_from_flash_data():
    
    # Read data
    display.print("INFO - Drawing path using saved GPS points")
    display.erase()
    color = color565(0, 255, 0)
    try:
        draw_gps_track(GPS_TRACK_FILE_PATH, display,color, width=240, height=320)
    except Exception as e:
        display.print(e)


def _get_barometer_readings():
    
    try:
        # Initialize BME280 sensor
        bme = BME280(i2c=softI2C1)
        
        # Read sensor data
        tempC = bme.temperature
        hum = bme.humidity
        pres = bme.pressure
        altitude = bme.altitude
        
        # Convert temperature to fahrenheit
        tempF = (bme.read_temperature()/100) * (9/5) + 32
        tempF = str(round(tempF, 2)) + 'F'
        
        return float(tempC.strip("C")), float(hum.strip("%")), float(pres.strip("hPa")), float(altitude)
        
        
    except Exception as e:
        # Handle any exceptions during sensor reading
        print('An error occurred:', e)

def _connect_to_wifi_():
    # Wi-Fi credentials
    display.erase()
    ssid = '90degrees'
    password = 'changeseverytime#02'

    # Init Wi-Fi Interface
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Connect to your network
    wlan.connect(ssid, password)

    # Wait for Wi-Fi connection
    connection_timeout = 10
    while connection_timeout > 0:
        if wlan.status() >= 3:
            break
        connection_timeout -= 1
        display.print('>> Waiting for Wi-Fi connection...')
        print('Waiting for Wi-Fi connection...')
        sleep(1)

    # Check if connection is successful
    if wlan.status() != 3:
        raise RuntimeError('Failed to establish a network connection')
    else:
        display.print('>> Connection successful!')
        print('\nConnection successful!')
        network_info = wlan.ifconfig()
        display.print('IP address: {}'.format(network_info[0]))
        print('>> IP address:', network_info[0])
        
    # Sync time from NTP (defaults to pool.ntp.org)
    try:
        sleep(2)
        ntptime.settime()
        display.print('>> Initializing ..\nWait 4 seconds ... ')
        sleep(4)
    except Exception as e:
        print(e)
        display.print('>> Error in setting NTP time')
        sleep(2)
        

        
def _send_weather_data_to_base():
    
    # Make GET request
    display.erase()
    display.print('\n>> Sending weather data to base station ...')
    
    tempC,humidity,pressure,altitude = _get_barometer_readings()
    url = "http://192.168.0.104:8080/api/v1/weather/push/10"
    data = {
        "nodeId": 10,
        "humidity": humidity,
        "temperature": tempC,
        "altitude": altitude,
        "airPressureInHpa": pressure,
        "time": int(time.time())
    }
    
    
    # Print local time
    display.print("Time from NTP (UTC): {}".format(str(time.localtime())))
    display.print(str(int(time.time() - (5.5 * 3600))))
    
    
    # Send POST request with JSON body
    try:
        response = requests.post(url, json=data, timeout=10)

        # Print response status and content
        
        print("Status Code:", response.status_code)
        print("Response Body:", response.text)
        display.print('\n>> Response from solo server : {}'.format(response.status_code))
        for key, value in response.headers.items():
            if(key == "Date"):
                display.print('>> Response time from server : \n{}'.format(str(value)))
                
    except Exception as e:
        display.print(str(e))
        
        
def _send_ping_data_via_lora(rx_node_address,data):
    
    display.print('\n>> Sending ping data via LoRa module...')
    
    lora = RYLR998(lora_uart1)
    if(lora.pulse):
        display.set_pos(USER_EDIT_TEXT_SCREEN_X_CURSOR_POS, USER_EDIT_TEXT_SCREEN_Y_CURSOR_POS)
#         display.print('\n>> TX details'.format(lora.address))
#         display.print('Network ID : {}\nNode Address : {}\nFrequency band : {} MHz\nRF parameters : {}'.format( \
#                 lora.networkid, lora.address, lora.band / 1000000 , lora.rf_parameters))
#         display.print('>> Transmitting packets ... ')
#         display.print('\n>> Receiver parameters : \nRX address : {}'.format(rx_node_address))
        display.print(str(lora.send(rx_node_address, str(data).encode("ascii"))))
        display.erase(int(display.width), int(display.height/2))
        display.set_pos(0,0)
#         display.print(str(data))
    else:
        display.print('LoRa radio module not communicating back')
        
        
def _initialize_lora_radio():

    # Send a device ID request (depends on your device protocol)
    print("Initializing lora device ")
#     lora_uart1.write(b'AT+PARAMETER=11,9,4,12\r\n')
    lora_uart1.write(b'AT+PARAMETER=9,7,1,12\r\n')  

    # Wait for a response (adjust timeout if needed)
    time.sleep(0.1)

    # Read available data
    if lora_uart1.any():
        response = lora_uart1.read()
        print(response)
    else:
        print("No response from device.")

def draw_rect(display, x1, y1, w, h, color):
    # Top and bottom edges
    for x in range(x1, x1 + w):
        display.pixel(x, y1, color)          # Top
        display.pixel(x, y1 + h - 1, color)  # Bottom
    # Left and right edges
    for y in range(y1, y1 + h):
        display.pixel(x1, y, color)          # Left
        display.pixel(x1 + w - 1, y, color)  # Right

def _draw_keyboard_layout(display):
    display.erase()

    display_width = 240
    keyboard_height = 160            # Total height of keyboard
    row_height = keyboard_height // len(rows)  # 160 / 4 = 40
    start_y_offset = 320 - keyboard_height     # Draw from y=160 to y=320

    green = color565(0, 255, 0)
    text_color = color565(255, 255, 255)      # white

    for row_index, row in enumerate(rows):
        num_keys = len(row)
        box_width = display_width // num_keys
        y = start_y_offset + row_index * row_height  # Shift down

        for col_index, key in enumerate(row):
            x = col_index * box_width

            # Draw box
            if(key == "<"):
                key = 'DEL'
                draw_rect(display, x, y, box_width + 7, row_height, green)
            elif(key == ">"):
                key = 'ENT'
                draw_rect(display, x, y, box_width + 7, row_height, green)
            elif(key == " "):
                key = 'SPACE'
                draw_rect(display, x, y, box_width, row_height, green)
            else:
                draw_rect(display, x, y, box_width, row_height, green)


            # Center text in box
            text_x = x + box_width // 2 - 4   # Adjust for char width
            text_y = y + row_height // 2 - 6  # Adjust for char height
            display.set_pos(text_x, text_y)
            display.print(key)



            
def startup():
    # _setup_compass_polygon()
    # _draw_tab(0, 0, width=240, height=12)
    _initialize_sd_card()
    # _clear_track_file()
    # _save_gps_data_to_flash()
               
    _connect_to_wifi_()
    _initialize_lora_radio()
#     
#     _setup_compass_polygon()
    _draw_keyboard_layout(display)
    
    try:
        while True:
            idle()

    except KeyboardInterrupt:
        print("\nCtrl-C pressed.  Cleaning up and exiting...")
    finally:
        display.cleanup()
    
    



def loop():
    looop_count = 0
    pressed_switch = detect_switch_pressed()
    press_count = 0
    while(pressed_switch == "N"):
        looop_count += 1
        display.set_pos(0,0)
#         _get_barometer_readings()
        _draw_compass_heading_line()
        
        
        pressed_switch = detect_switch_pressed()
        if(pressed_switch == "U"):
            display.print("INFO - Up key pressed")
            _clear_track_file()
            pressed_switch == "N"
            
        elif(pressed_switch == "M"):
            display.print("INFO - Mid key pressed")
            press_count += 1
            pressed_switch = "N"
            
        elif(pressed_switch == "D" ):
            display.print("INFO - Down key pressed")
            display.erase()
            _draw_gps_track_from_flash_data()
            pressed_switch = "N"
            press_count = 0
            
        if(press_count >= 1 ):
            _save_gps_data_to_flash()
               
#         sleep(5)
#         _send_weather_data_to_base()
#         data = time.localtime()
#         _send_ping_data_via_lora(LORA_RX_NODE_ADDRESS,data)


            
    
#     _draw_gps_track_from_flash_data()
#     osm_file_path="/sd/urban.txt"
#     get_points_from_osm_file(osm_file_path,display,color565(0, 255, 0))

#     
#     while(1):
#         _draw_compass_heading_line()
        
startup()
# loop()
    

        

    
    














