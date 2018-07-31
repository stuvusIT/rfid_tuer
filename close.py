#!/usr/bin/python3

import pifacedigitalio
from threading import Lock, Thread
from time import sleep
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.Exceptions import CardConnectionException, NoCardException
from smartcard.util import toHexString
from ldap3 import Server, Connection, ALL
import yaml
from datetime import datetime
from door import Door
from util import read_config

def main():
    output_pins, input_pins, relay_number, ldap_match_attr, ldap_server, ldap_port, ldap_base_dn, ldap_use_ssl, ldap_user, ldap_user_secret = read_config("config.yml")
    pifacedigital = pifacedigitalio.PiFaceDigital()
    door = Door(pifacedigital, output_pins, input_pins, relay_number)
    door.close()

if __name__ == "__main__":
    main()

