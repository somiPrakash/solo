# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-w-wi-fi-micropython/

import network
import requests
from time import sleep
# Wi-Fi credentials
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
    print('Waiting for Wi-Fi connection...')
    sleep(1)

# Check if connection is successful
if wlan.status() != 3:
    raise RuntimeError('Failed to establish a network connection')
else:
    print('Connection successful!')
    network_info = wlan.ifconfig()
    print('IP address:', network_info[0])
    
    
# Make GET request
response = requests.get("https://raw.githubusercontent.com/RuiSantosdotme/Random-Nerd-Tutorials/master/Projects/Raspberry-Pi-Pico/MicroPython/Connect_to_Wi-Fi.py")
# Get response code
response_code = response.status_code
# Get response content
response_content = response.text

# Print results
print('Response code: ', response_code)
print('Response content:', response_content)

