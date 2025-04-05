import machine
from time import sleep

# Define the UART pins and create a UART object
gps_serial = machine.UART(0, baudrate=9600, tx=0, rx=1)

while True:
    if gps_serial.any():
        line = gps_serial.readline()  # Read a complete line from the UART
        if line:
            try:
                line = line.decode('utf-8')
                print(line.strip())
            except Exception as e:
                print("")
    sleep(0.5)
