#!/usr/bin/env python

from logging import getLogger, Formatter, StreamHandler, DEBUG
import argparse
import copy
import collections
import json
import os
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

IPIP_IFL = 'ip-0/0/0.0'

##
DEFAULT_TOPIC = '#'
SYSLOG_TOPIC_HEADER = r"/junos/events/syslog"
MQTT_PORT = 1883
MQTT_IP = '127.0.0.1'
MQTT_TIMEOUT = 180

logger = getLogger(__name__)
handlers = collections.defaultdict(set)

external_interface = None
interface_address = None
need_update = False

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
    ifl = str(ifd + '.' + subunit).strip()
    family = str(message['jet-event']['attributes']['family']).strip()
    address = str(message['jet-event']['attributes']['local-address']).strip().split('/')[0]

    logger.info("Received IFA update: event: {0}, ifl: {1}, family: {2}, address: {3}".format(event_id, ifl, family, address))
    logger.info("Current ifl: {0}, address: {1}".format(external_interface, interface_address))
    print(event_id == 'KERNEL_EVENT_IFA_ADD')
    print(event_id == 'KERNEL_EVENT_IFA_CHANGE')
    print(family == 'inet6')
    print(ifl == external_interface)
    print(address != interface_address)

    if event_id == 'KERNEL_EVENT_IFA_ADD' or event_id == 'KERNEL_EVENT_IFA_CHANGE':
        if family == 'inet6' and ifl == external_interface and address != interface_address:
            logger.info("External Interface IPv6 address is changed. {0} -> {1}".format(interface_address, address))
            interface_address = address
            need_update = True

def update_configuration():
    logger.info("update")

def main():
    global external_interface
    global interface_address
    global need_update

    handler = StreamHandler()
    handler.setFormatter(Formatter(LOG_FORMAT))
    logger.addHandler(handler)

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
        logger.setLevel(DEBUG)

    device = Device()
    device.open()

    external_interface = args.external_interface
    logger.debug("External interface: %s" % external_interface)

    interface_address = junos.get_interface_address(device, external_interface)
    if(interface_address == None):
        logger.error("Interface has no IPv6 address!")
        exit(2)

    try:
        mqtt_client = open_mqtt()
        subscribe(mqtt_client, createCustomTopic('/junos/events/kernel/interfaces/ifa/#'), ifa_cb)
        while True:
            time.sleep(0.1)
            if need_update:
                need_update = False
                update_configuration()

    except Exception as ex:
        pass


if __name__ == '__main__':
    main()
