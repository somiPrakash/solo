from machine import Pin, I2C , UART
import time


# Define I2C bus (I2C0 on GP8=SDA, GP9=SCL)
i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=100000)

# Scan for devices
devices = i2c.scan()

# Print results
if devices:
    print("I2C devices found:", [hex(d) for d in devices])
else:
    print("No I2C devices found")


# Initialize UART1: TX=GP4, RX=GP5 (default UART1 pins)
uart1 = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))

# Wait a moment for UART setup
time.sleep(0.1)

# Send a device ID request (depends on your device protocol)
uart1.write(b'AT+PARAMETER=11,9,4,12\r\n')   # Example SCPI command, replace as needed

# Wait for a response (adjust timeout if needed)
time.sleep(0.1)

# Read available data
if uart1.any():
    response = uart1.read()
    print(response)
else:
    print("No response from device.")

