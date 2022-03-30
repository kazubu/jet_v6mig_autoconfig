#!/usr/bin/env python

from datetime import datetime
from logging import getLogger, Formatter, StreamHandler
import argparse
import copy
import collections
import json
import os
import random
import sys
import time

from paho.mqtt import client as mqtt

from jnpr.junos import Device
import v6mig_autoconfig.v6mig.junos_utils as junos
import v6mig_autoconfig.v6mig.v6mig as v6mig

DNS_SERVERS = {
        "NTT_EAST": ['2404:1a8:7f01:a::3', '2404:1a8:7f01:b::3'],
        "NTT_WEST": ['2001:a7ff:5f01::a', '2001:a7ff:5f01:1::a']
        }

VENDOR_ID = '000000-kazubu'
PRODUCT = 'v6mig_autoconfig'
VERSION = '0_0_1'
CAPABILITY = 'dslite'

LOG_FORMAT = "[%(asctime)s] [%(levelname)s][%(name)s:%(lineno)s][%(funcName)s]: %(message)s"

DEFAULT_IPIP_IFL = 'ip-0/0/0.0'

##
DEFAULT_TOPIC = '#'
SYSLOG_TOPIC_HEADER = r"/junos/events/syslog"
MQTT_PORT = 1883
MQTT_IP = '127.0.0.1'
MQTT_TIMEOUT = 180

logger = getLogger(__name__)
handlers = collections.defaultdict(set)

##
next_update = None
provisioned_ttl = None
need_update = False

##
external_interface = None
interface_address = None
dns_servers = None
insecure = False
ipip_ifl = None

## MQTT
def createCustomTopic(event_id = DEFAULT_TOPIC):
    data = {}
    data['event_id'] = event_id
    data['topic'] = "{0}".format(event_id)
    data['subscribed'] = 0
    return data

def subscribe(mqtt_client, subscriptionType, handler = None, qos = 0):
    global handlers
    topic = subscriptionType['topic']
    print("topic: " + str(topic))
    mqtt_client.subscribe(topic)
    subscriptionType['subscribed'] = 1
    if(handler):
        handlers[topic].add(handler)

def mqtt_on_message_cb(client, obj, msg):
    payload = msg.payload
    topic = msg.topic
    json_data = None
    decoder = json.JSONDecoder()

    json_data, end = decoder.raw_decode(payload.decode('utf-8'))

    if(json_data is None):
        print("err")
    if(len(payload) != end):
        print("err")

    callback_called = False
    for cbs in handlers:
        if cbs != '#':
            if mqtt.topic_matches_sub(cbs, topic):
                for cb in handlers.get(cbs, []):
                    cb(json_data)
                    callback_called = True

    if callback_called is False:
        # no specific callback
        for cb in handlers.get('#', []):
            cb(json_data)

def open_mqtt(device = MQTT_IP, port = MQTT_PORT, keepalive = MQTT_TIMEOUT):
    try:
        mqtt_client = mqtt.Client()
        mqtt_client.connect(device, port, keepalive)
        mqtt_client.loop_start()
        mqtt_client.on_message = mqtt_on_message_cb
    except Exception:
        message = 'Could not connect to MQTT'
        raise Exception(message)

    return mqtt_client

def ifa_cb(message):
    global need_update
    global interface_address
    event_id = str(message['jet-event']['event-id']).strip()
    ifd = str(message['jet-event']['attributes']['name']).strip()
    subunit = str(message['jet-event']['attributes']['subunit']).strip()
    family = str(message['jet-event']['attributes']['family']).strip()
    address = str(message['jet-event']['attributes']['local-address']).strip().split('/')[0]
    ifl = ifd + '.' + subunit

    logger.debug("Received IFA update: event: {0}, ifl: {1}, family: {2}, address: {3}".format(event_id, ifl, family, address))

    if event_id == 'KERNEL_EVENT_IFA_ADD' or event_id == 'KERNEL_EVENT_IFA_CHANGE':
        if family == 'inet6' and ifl == external_interface and address[0:4] != 'fe80' and address != interface_address:
            logger.info("External Interface IPv6 address is changed: {0} -> {1}.".format(interface_address, address))
            interface_address = address
            need_update = True

def current_time():
    """
    Return current UTC UNIX Time.
    """
    return int(datetime.utcnow().timestamp())

def check_time(time):
    """
    Return True if specified UTC UNIX time is just now.
    """
    return current_time() == time

def random_interval(minimum, maximum):
    """
    Return random value between minimum to maximum.
    """
    return int((maximum - minimum) * random.random() + minimum)

def set_next_update(interval):
    """
    Set next update timing to current time + specified interval(minutes).
    """
    global next_update
    next_update = int(current_time() + interval * 60)

def update_configuration(device):
    """
    Try to retrieve provisioning information from provisioning server and apply to configuration if needed.
    """
    global provisioned_ttl

    logger.info("Update process is started.")
    logger.debug("DNS Servers: %s" % ', '.join(dns_servers))

    ps = v6mig.discover_provisioning_server(copy.copy(dns_servers))
    logger.debug("Provisioning server: %s" % ps)

    if(ps):
        pd = v6mig.get_provisioning_data(provisioning_server = ps, nameservers = copy.copy(dns_servers), vendorid = VENDOR_ID, product = PRODUCT, version = VERSION, capability = CAPABILITY, insecure = insecure)
        logger.debug("Provisioning Data: %s" % pd)
    else:
        logger.error("Failed to retrieve provisioning server.")
        # TODO: need to care next update timing for DNS failure.
        return False

    if(pd):
        aftr = v6mig.get_aftr_address(pd, copy.copy(dns_servers), multiple = True)
    else:
        logger.error("Failed to retrieve provisioning data.")
        return False

    if(len(aftr)):
        logger.debug("AFTR(s): %s", str(aftr))

        if len(aftr) > 1:
            current_aftr = junos.get_current_ipip_destination(device = device, ifl = ipip_ifl)
            logger.debug("Current configured AFTR: %s", current_aftr)
            selected_aftr = current_aftr if current_aftr in aftr else aftr[0]
        else:
            selected_aftr = aftr[0]

        logger.debug("Selected AFTR: %s" % selected_aftr)
        config = junos.generate_dslite_configuration(ifl = ipip_ifl, aftr = selected_aftr, source_address = interface_address)

        logger.debug("Generated configuration:\n%s", config)
    else:
        logger.error("Failed to retrieve AFTR IP address.")
        return False

    if(pd['ttl']):
        provisioned_ttl = int(pd['ttl'])
        logger.debug("TTL: %s" % provisioned_ttl)

    junos.update_configuration(device, config)
    return True

def main():
    global need_update
    global external_interface
    global interface_address
    global ipip_ifl
    global dns_servers
    global insecure

    root_logger = getLogger()

    handler = StreamHandler()
    handler.setFormatter(Formatter(LOG_FORMAT))
    root_logger.addHandler(handler)

    getLogger('v6mig_autoconfig.v6mig.junos_utils.main').setLevel('INFO')
    getLogger('v6mig_autoconfig.v6mig.v6mig.main').setLevel('INFO')

    logger.info("Start v6mig_autoconfig")
    parser = argparse.ArgumentParser()
    parser.add_argument('--external-interface', required=True)
    parser.add_argument('--dns-from-dhcpv6')
    parser.add_argument('--area')
    parser.add_argument('--insecure')
    parser.add_argument('--debug')
    parser.add_argument('--ipip-ifl')

    args = parser.parse_args()
    if(args.dns_from_dhcpv6 is None and args.area is None):
        logger.error("Option --dns-from-dhcpv6 or --area [AREA] is required.")
        exit(1)

    if(args.debug):
        logger.setLevel('DEBUG')
        getLogger('v6mig_autoconfig.v6mig.junos_utils.main').setLevel('DEBUG')
        getLogger('v6mig_autoconfig.v6mig.v6mig.main').setLevel('DEBUG')

    external_interface = args.external_interface
    logger.debug("External interface: %s" % external_interface)

    insecure = True if args.insecure else False
    ipip_ifl = args.ipip_ifl if args.ipip_ifl else DEFAULT_IPIP_IFL

    device = Device()
    device.open()

    while True:
        interface_address = junos.get_interface_address(device, external_interface)
        if(interface_address == None):
            logger.error("Interface has no IPv6 address! Retrying...")
            time.sleep(5)
        else:
            logger.debug("Interface address: %s" % interface_address)
            break

    if(args.area):
        if(args.area in DNS_SERVERS):
            dns_servers = DNS_SERVERS[args.area]
        else:
            logger.error("Area %s is not found! exit." % args.area)
            exit(1)
    else:
        dns_servers = junos.get_dhcpv6_dns_servers(device, external_interface)

    if(dns_servers is None):
        logger.error("DNS Server is not set. exit.")
        exit(2)

    logger.debug("DNS Servers: %s" % ', '.join(dns_servers))

    try:
        mqtt_client = open_mqtt()
        subscribe(mqtt_client, createCustomTopic('/junos/events/kernel/interfaces/ifa/#'), ifa_cb)

        need_update = True
        while True:
            time.sleep(0.1)
            if check_time(next_update):
                logger.info("Scheduled update will be executed.")
                need_update = True

            if need_update:
                need_update = False
                if update_configuration(device):
                    if(provisioned_ttl):
                        interval = int(provisioned_ttl / 60)
                    else:
                        interval = random_interval(minimum = 60 * 20, maximum = 60 * 24)

                    set_next_update(interval)
                    logger.info("Update is succeeded or not changed. Wait %s minutes for next update."% str(interval))
                else:
                    interval = random_interval(minimum = 10, maximum = 30)
                    set_next_update(interval)
                    logger.info("Update is failed. Wait %s minutes for next update." % str(interval))

    except Exception as ex:
        print(ex)
        pass


if __name__ == '__main__':
    main()
