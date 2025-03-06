#!/bin/env python3

import paho.mqtt.client as mqtt
import subprocess
import sys
import time

MQTT_SERVER = "mqtt"
TOPIC = "MyFirewall"
TABLE = "TABLE"

def errPrint(buf):
  sys.stderr.write(buf)
  sys.stderr.flush()

## MQTT Event Handlers
def on_connect(client, userdata, flags, rc):
  errPrint(f"MQTT: Connected with result code {str(rc)}\n")
  client.subscribe(f"{TOPIC}/{TABLE}/block")

def on_log(client, userdata, level, buff):
  if level != 16:
    errPrint(f"MQTT: {level} : {buff}\n")

def on_message(client, userdata, msg):
  if msg.payload == b"1":
    if not isblocked():
      errPrint("Enabling block\n")
      res = subprocess.run(["/usr/sbin/iptables", "-A", TABLE, "-j", "DROP"])
      res = subprocess.run(["/usr/sbin/ip6tables", "-A", TABLE, "-j", "DROP"])
  elif msg.payload == b"0":
    errPrint("Disabling block\n")
    res = subprocess.run(["/usr/sbin/iptables", "-F", TABLE])
    res = subprocess.run(["/usr/sbin/ip6tables", "-F", TABLE])
  client.publish(f"{TOPIC}/{TABLE}/blocked", isblocked(), retain=True)

def isblocked():
  res = subprocess.check_output(["/usr/sbin/iptables", "-L", TABLE, "1"])
  return res.decode().startswith("DROP")

def main():
  global TABLE
  if len(sys.argv) > 1:
    TABLE = sys.argv[1]
  else:
    errPrint(f"Warning: using default name {TABLE}\n")
  client = mqtt.Client()
  client.on_connect = on_connect
  client.on_message = on_message
  client.on_log = on_log
  client.connect(MQTT_SERVER, 1883, 60)
  client.publish(f"{TOPIC}/{TABLE}/blocked", isblocked(), retain=True)
  client.loop_forever()

if __name__ == '__main__':
  main()
