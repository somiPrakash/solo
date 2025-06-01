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
import sdcardlib
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

# Debug print SD card directory and files
print(os.listdir('/sd'))

# Create / Open a file in write mode.
# Write mode creates a new file.
# If  already file exists. Then, it overwrites the file.
file = open("/sd/sample.txt","w")

# Write sample text
for i in range(20):
    file.write("Sample text = %s\r\n" % i)
    
# Close the file
file.close()



# Open the file in "read mode". 
# Read the file and print the text on debug port.
file = open("/sd/sample.txt", "r")
if file != 0:
    print("Reading from SD card")
    read_data = file.read()
    print (read_data)
file.close()
































