#!/usr/bin/python3

import pifacedigitalio
from threading import Lock, Thread
from time import sleep
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.Exceptions import CardConnectionException, NoCardException
from smartcard.util import toHexString
from ldap3 import Server, Connection, ALL
import yaml

lock = Lock()
class Door(object):
    def __init__(self, pifacedigital, output_pins, input_pins, relay_number ):
        self.pifacedigital = pifacedigital
        self.door_switch_green_led_output_pin = output_pins[0]
        self.door_switch_red_led_output_pin = output_pins[1]
        self.rfid_reader_red_led_output_pin = output_pins[2]
        self.rfid_reader_green_led_output_pin = output_pins[3]
        self.door_state_input_pin = input_pins[0]
        self.door_relay_number = relay_number
        self.state = False

    def update_leds(self):
        global lock
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
                sleep(0.5)

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
        global lock
        lock.acquire()
        self.state = False
        self.pifacedigital.relays[self.door_relay_number].turn_off()
        lock.release()
        self.update_leds()

    def open(self):
        global lock
        lock.acquire()
        self.state = True
        self.pifacedigital.relays[self.door_relay_number].turn_on()
        lock.release()
        self.update_leds()

    def is_locked(self):
        status = not bool(self.pifacedigital.input_pins[self.door_state_input_pin].value)
        return status

    def event_on_door_switch(self, event):
        self.toggle()

from parseATR import match_atr_differentiated
def parseATRTuer(ATR):
    card = match_atr_differentiated(ATR)
    if card:
        # exact match
        if ATR in card:
            return card[ATR]
            # remove the entry so it is not displayed as "RE match"
            del card[ATR]
    else:
        return False


class PrintObserver(CardObserver):
    """A simple card observer that is notified
    when cards are inserted/removed from the system and
    prints the list of cards
    """

    def __init__(self, door, ldap_base_dn, ldap_server, ldap_port, ldap_use_ssl, ldap_user, ldap_user_secret, ldap_match_attr):
        self.door = door
        self.ldap_base_dn = ldap_base_dn
        self.ldap_match_attr = ldap_match_attr
        self.server = Server(ldap_server, port=ldap_port, use_ssl=ldap_use_ssl)
        self.conn = Connection(self.server, ldap_user, ldap_user_secret, auto_bind=True)

    def update(self, observable, actions):
        (addedcards, removedcards) = actions
        for card in addedcards:
            try:
                card.connection = card.createConnection()
                card.connection.connect()
                card_id_hex = toHexString(card.connection.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])[0])
                card_type = "test" #parseATRTuer(toHexString(card.atr))[0]
                self.conn.search(self.ldap_base_dn, '({}=*)'.format(self.ldap_match_attr), attributes=[self.ldap_match_attr])
                print("Connection from {} using a {} card".format(card_id_hex, card_type))
                for entry in self.conn.entries:
                    value_to_compare = str(entry[self.ldap_match_attr]).strip()
                    if value_to_compare == card_id_hex.strip():
                        print("toggle door")
                        self.door.toggle()
            except CardConnectionException:
                print("Error reading card carrying on")
            except NoCardException:
                print("Error reading card carrying on")

#def main():
    output_pins = [0, 1, 2, 3]
    input_pins = [0]
    with open("config.yml", 'r') as stream:
        config = yaml.load(stream)
        output_pins[0] = config['door_switch_green_led_output_pin']
        output_pins[1] = config['door_switch_red_led_output_pin']
        output_pins[2] = config['rfid_reader_green_led_output_pin']
        output_pins[3] = config['rfid_reader_red_led_output_pin']
        input_pins[0] = config['door_state_input_pin']
        relay_number = config['door_relay_number']
        ldap_match_attr = config['ldap_match_attr']
        ldap_server = config['ldap_server']
        ldap_port = config['ldap_port']
        ldap_base_dn = config['ldap_base_dn']
        ldap_use_ssl = config['ldap_use_ssl']
        ldap_user = config['ldap_user']
        ldap_user_secret = config['ldap_user_secret']
    
    pifacedigital = pifacedigitalio.PiFaceDigital()
    door = Door(pifacedigital, output_pins, input_pins, relay_number)
    listener = pifacedigitalio.InputEventListener(chip=pifacedigital)
    listener.register(1, pifacedigitalio.IODIR_RISING_EDGE, door.event_on_door_switch)
    listener.activate()
    door.close()
    cardmonitor = CardMonitor()
    cardobserver = PrintObserver(door, ldap_base_dn, ldap_server, ldap_port, ldap_use_ssl, ldap_user, ldap_user_secret, ldap_match_attr)
    cardmonitor.addObserver(cardobserver)

    while True:
        sleep(60)
    cardmonitor.deleteObserver(cardobserver)

if __name__ == "__main__":
    main()

