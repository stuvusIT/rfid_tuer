import yaml

def read_config(config_name):
    output_pins = [0, 1, 2, 3]
    input_pins = [0]
    with open(config_name, 'r') as stream:
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
    return output_pins, input_pins, relay_number, ldap_match_attr, ldap_server, ldap_port, ldap_base_dn, ldap_use_ssl, ldap_user, ldap_user_secret
