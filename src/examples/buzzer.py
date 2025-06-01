

import time
import machine

def main():


    print("Insert Grove-Buzzer to Grove-Base-Hat slot PWM[12 13 VCC GND]")
    # Grove Base Hat for Raspberry Pi
    pin = 9
    bz = machine.Pin(9,machine.Pin.OUT)

    # create PWM instance
    pwm = GPIO.PWM(pin, 10)
    pwm.start(0) 

    chords = [1047, 1175, 1319, 1397, 1568, 1760, 1976]
    # Play sound (DO, RE, MI, etc.), pausing for 0.5 seconds between notes
    try:
        for note in chords:
            pwm.ChangeFrequency(note)
            pwm.ChangeDutyCycle(95)
            time.sleep(0.5) 
    finally:
        pwm.stop()
        GPIO.cleanup()

    print("Exiting application")

if __name__ == '__main__':
    main()