import os
map_file="/Users/somiprakash/Documents/projects/solo/sample_data/map.txt"


'''
 # Demonstrates RPi Pico interface to MicroSD Card Adapter
 # Create a text file and write running numbers.
 # Open text file, read and print the content on debug port
   
 * The Raspberry Pi Pico pin connections for MicroSD Card Adapter SPI
 
 # MicroSD Card Adapter Power Pins
 * MicroSD VCC pin to Pico VBUS
 * MicroSD  GND pin to Pico GND
 
 # MicroSD SPI Pins
 * MicroSD MISO pin to Pico GPIO-12
 * MicroSD MOSI pin to Pico GPIO-11
 * MicroSD SCK pin to Pico GPIO-10
 * MicroSD CS pin to Pico GPIO-13
 
 Name:- M.Pugazhendi
 Date:-  28thJul2021
 Version:- V0.1
 e-mail:- muthuswamy.pugazhendi@gmail.com
 
cspin = machine.Pin(8,machine.Pin.OUT)
dio0 = machine.Pin(6,machine.Pin.IN)
rst = machine.Pin(7,machine.Pin.OUT)
spi = machine.SPI(0,
                  baudrate=2000000,
                  polarity=1,
                  phase=1,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(18),
                  mosi=machine.Pin(19),
                  miso=machine.Pin(16))
'''
import machine
from src.storage import sdcardlib
import os

# Initialize the SD card
spi = machine.SPI(0,
                  baudrate=2000000,
                  polarity=1,
                  phase=1,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(18),
                  mosi=machine.Pin(19),
                  miso=machine.Pin(16))

sd=sdcardlib.SDCard(spi,machine.Pin(20))



# Create a instance of MicroPython Unix-like Virtual File System (VFS),
vfs=os.VfsFat(sd)
 
# Mount the SD card
os.mount(sd,'/sd')





# Open the file in "read mode". 
# Read the file and print the text on debug port.
# file = open("/sd/map.txt", "r")
# if file != 0:
#     print("Reading from SD card")
#     line = file.readline()
#     while(line):
#         line = file.readline()
#         print (line)
# file.close()
# 
# 

osm_file_path="/sd/map.txt"

def nmea_to_decimal(nmea_str):
    nmea = float(nmea_str)
    degrees = int(nmea // 100)
    minutes = nmea - degrees * 100
    return degrees + minutes / 60





def _get_points_from_osm_file(osm_file_path):
    nodes = []
    polygon_list = []
    try:
        with open(osm_file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line.startswith("<node") and line.endswith("/>"):
                    node = {}
                    parts = line.split()
                    for part in parts:
                        if "=" in part:
                            key, value = part.split("=", 1)
                            value = value.strip('"').strip('/>')
                            if(key == "lat"):
                                lat = nmea_to_decimal(value.replace('"',""))
                            elif(key == "lon" ):
                                lon = nmea_to_decimal(value.replace('"',""))
                            elif(key == "id"):
                                id = int(value)
                    if(len(nodes) < 256):
                        nodes.append((lat,lon))
                    
                elif line.startswith("</node>"):
                    print(nodes)
                    nodes = []
                    
                elif line.startswith("<bounds") and line.endswith("/>"):
                    parts = line.split()
                    for part in parts:
                        if "=" in part:
                            key, value = part.split("=", 1)
                            value = value.strip('"').strip('/>')
                            if(key == "minlat"):
                                minlat = nmea_to_decimal(value.replace('"',""))
                            elif(key == "minlon" ):
                                minlon = nmea_to_decimal(value.replace('"',""))
                            elif(key == "maxlat"):
                                maxlat = nmea_to_decimal(value.replace('"',""))
                            elif(key == "maxlon"):
                                maxlon = nmea_to_decimal(value.replace('"',""))
                                
                                
                        
                    
    except Exception as e:
        print(len(nodes))
        print(e)
        
    
    return polygon_list,[(minlat,minlon),(maxlat,maxlon)]



        
polygon_list,bounding_box = _get_points_from_osm_file(osm_file_path)



print(bounding_box)

