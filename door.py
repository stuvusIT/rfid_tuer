from threading import Lock, Thread
from time import sleep

class Door(object):
    def __init__(self, pifacedigital, output_pins, input_pins, relay_number ):
        self.lock = Lock()
        self.pifacedigital = pifacedigital
        self.door_switch_green_led_output_pin = output_pins[0]
        self.door_switch_red_led_output_pin = output_pins[1]
        self.rfid_reader_red_led_output_pin = output_pins[2]
        self.rfid_reader_green_led_output_pin = output_pins[3]
        self.door_state_input_pin = input_pins[0]
        self.door_relay_number = relay_number
        self.state = False

    def update_leds(self):
        if self.state:
            self.pifacedigital.leds[self.door_switch_red_led_output_pin].turn_on()
            self.pifacedigital.leds[self.rfid_reader_red_led_output_pin].turn_on()
            self.pifacedigital.leds[self.door_switch_green_led_output_pin].turn_off()
            self.pifacedigital.leds[self.rfid_reader_green_led_output_pin].turn_off()
        else:
            self.pifacedigital.leds[self.door_switch_green_led_output_pin].turn_on()
            self.pifacedigital.leds[self.rfid_reader_green_led_output_pin].turn_on()
            self.pifacedigital.leds[self.door_switch_red_led_output_pin].turn_off()
            self.pifacedigital.leds[self.rfid_reader_red_led_output_pin].turn_off()
            while True:
                if self.is_locked() or self.state:
                    break
                self.pifacedigital.leds[self.door_switch_red_led_output_pin].toggle()
                self.pifacedigital.leds[self.rfid_reader_red_led_output_pin].toggle()
                self.pifacedigital.leds[self.door_switch_green_led_output_pin].toggle()
                self.pifacedigital.leds[self.rfid_reader_green_led_output_pin].toggle()
                sleep(0.25)

            if not self.state:
                self.pifacedigital.leds[self.door_switch_green_led_output_pin].turn_on()
                self.pifacedigital.leds[self.rfid_reader_green_led_output_pin].turn_on()
                self.pifacedigital.leds[self.door_switch_red_led_output_pin].turn_off()
                self.pifacedigital.leds[self.rfid_reader_red_led_output_pin].turn_off()

    def toggle(self):
        if self.state:
            self.close()
        else:
            self.open()

    def close(self):
        self.lock.acquire()
        self.state = False
        self.pifacedigital.relays[self.door_relay_number].turn_off()
        self.lock.release()
        self.update_leds()

    def open(self):
        self.lock.acquire()
        self.state = True
        self.pifacedigital.relays[self.door_relay_number].turn_on()
        self.lock.release()
        self.update_leds()

    def is_locked(self):
        status = not bool(self.pifacedigital.input_pins[self.door_state_input_pin].value)
        return status

    def event_on_door_switch(self, event):
        self.toggle()
