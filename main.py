#!/usr/bin/python3

import pifacedigitalio
from threading import Lock, Thread
from time import sleep
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.Exceptions import CardConnectionException, NoCardException
from smartcard.util import toHexString
from ldap3 import Server, Connection, ALL
from datetime import datetime
from door import Door
from util import read_config
import logging
import sys

from parseATR import match_atr_differentiated
def parseATRTuer(ATR):
    card = match_atr_differentiated(ATR)
    if card:
        # exact match
        if ATR in card:
            return card[ATR] # remove the entry so it is not displayed as "RE match"
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
                card_type = "DESFireEV1" #parseATRTuer(toHexString(card.atr))[0]
                ldap_query = '({}=*)'.format(self.ldap_match_attr)
                self.conn.search(self.ldap_base_dn, ldap_query, attributes=[self.ldap_match_attr])
                logging.info("Connection from {} using a {} card".format(card_id_hex, card_type))
                found_match = False
                for entry in self.conn.entries:
                    value_to_compare = str(entry[self.ldap_match_attr]).strip()
                    pfusch = "".join(str(card_id_hex).split()).lower()
                    card_with_type = "DESFireEV1-{}".format(pfusch)
                    if value_to_compare == card_with_type:
                        logging.info("Toggle door")
                        found_match = True
                        self.door.toggle()
                        break
                if not found_match:
                    logging.warning("Unknown Tag: DESFireEV1-{}".format(card_id_hex.strip()))
            except CardConnectionException:
                logging.warning("Error reading card carrying on")
            except NoCardException:
                logging.warning("Error reading card carrying on")

def main():
    sys.stdout = open('door.log')
    output_pins, input_pins, relay_number, ldap_match_attr, ldap_server, ldap_port, ldap_base_dn, ldap_use_ssl, ldap_user, ldap_user_secret = read_config("config.yml")
    pifacedigital = pifacedigitalio.PiFaceDigital()
    door = Door(pifacedigital, output_pins, input_pins, relay_number)
    # To fix startup problems we toggle the lock
    door.close()
    sleep(0.5)
    door.open()
    sleep(0.5)
    door.close()
    listener = pifacedigitalio.InputEventListener(chip=pifacedigital)
    listener.register(1, pifacedigitalio.IODIR_ON, door.event_on_door_switch)
    listener.activate()
    cardmonitor = CardMonitor()
    cardobserver = PrintObserver(door, ldap_base_dn, ldap_server, ldap_port, ldap_use_ssl, ldap_user, ldap_user_secret, ldap_match_attr)
    cardmonitor.addObserver(cardobserver)

    while True:
        sleep(60)
    cardmonitor.deleteObserver(cardobserver)

if __name__ == "__main__":
    main()

