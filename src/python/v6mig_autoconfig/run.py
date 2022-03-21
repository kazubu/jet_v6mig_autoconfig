#!/usr/bin/env python
import argparse
import collections
import json
import os
import stat
import time

from paho.mqtt import client as mqtt

handlers = collections.defaultdict(set)

DEFAULT_TOPIC = '#'
SYSLOG_TOPIC_HEADER = r"/junos/events/syslog"
MQTT_PORT = 1883
MQTT_IP = '127.0.0.1'
MQTT_TIMEOUT = 180

def createSyslogTopic(event_id = DEFAULT_TOPIC):
    data = {}
    data['event_id'] = "syslog_" + event_id
    data['topic'] = "{0}/{1}".format(SYSLOG_TOPIC_HEADER, event_id)
    data['subscribed'] = 0
    return data

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

def syslog_cb(message):
    with open('/var/tmp/mqtt-log.txt', 'a') as f:
        print(message)
        print(message, file = f)

def main():
    try:
        print("[INFO] start")
        mqtt_client = open_mqtt()
        subscribe(mqtt_client, createCustomTopic(), syslog_cb)
        while True:
            time.sleep(0.1)


    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    main()
