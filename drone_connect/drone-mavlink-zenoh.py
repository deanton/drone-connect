import time
from pymavlink import mavutil
import paho.mqtt.client as mqtt
import zenoh, random, time
import os
import signal
import sys
import json


my_name = os.path.basename(__file__)

# Connect to the drone via MAVLink 
connection_string = 'udp:127.0.0.1:14550'
drone = mavutil.mavlink_connection(connection_string)

print("waiting for heartbeat")
result = drone.wait_heartbeat()
print(f"passed wait heartbeat\n{result}\n")

# Publish MAVLink telemetry to MQTT
def publish_telemetry():
    #config = zenoh.Config.from_file(path="client_cloud_config.json5")
    #session = zenoh.open(config=config)
    session = zenoh.open(zenoh.Config())
    #name = my_name.replace(".py", "")
    name = "001"
    #myhome/drone/*/mavlink/**
    #key = f"myhome/drone/{name}/"
    #pub = session.declare_publisher(key)
    print("in publish_telemetry")

    while True:
        
        #msg = drone.recv_match(type='BATTERY_STATUS', blocking=True)
        msg = drone.recv_match(blocking=True)

        if msg is None:
            continue
        #timestamp = drone.time_since(msg.message_type)
        print("---------------------------------")
        timestamp = time.time_ns()
        print(timestamp)
        print(msg)
        print(msg.to_dict())
        print(msg.get_type())
        msg_type = msg.get_type()
        a = msg.get_msgbuf()
        print(a)
        b = msg.get_fieldnames()
        print(b)
        print("---------------------------------")
        resource_key = f"myhome/drone/{name}/mavlink/{msg_type}"
        #to_send_msg = f"Timestamp: {timestamp}, Message: {msg.to_dict()}"
        message = msg.to_dict()
        #message["time"] = timestamp
        to_send_msg = json.dumps({
            "timestamp": timestamp,
            "message_type": msg_type,
            #"message": msg.to_dict()
            "message": message
        })
        #print(f"to_send_msg {to_send_msg}")
        session.put(resource_key, to_send_msg)

        # if msg:
        #     buf = f"{msg}"

        #     pub.put(buf)

        # print("requesting GPS_RAW_INT")
        # msg = drone.recv_match(type='GPS_RAW_INT', blocking=True)
        # print("got msg")
        # if msg:
        #     gps_data = {
        #         'lat': msg.lat / 1e7, # Convert to decimal degrees
        #         'lon': msg.lon / 1e7,
        #         'alt': msg.alt / 1000.0 # convert to meter
        #     }

        #     #mqtt_client.publish("/drone/telemetry/gps", str(gps_data))
        #     buf = f"{gps_data}"
        #     pub.put(buf)
        #     print(f"Published GPS data to MQTT: {gps_data}")
        
        time.sleep(1)

def handle_message(msg):
    if msg.get_type() == 'GPS_RAW_INT':
        gps_data = {
            'lat': msg.lat /1e7,
            'lon': msg.lon / 1e7,
            'alt': msg.alt / 1000.0
        }
        print(f"Received GPS data: {gps_data}")
    else:
        print(f"Received {msg}")


def listen_for_messages():
    while True:
        msg = drone.recv_match(blocking=True)
        if msg:
            handle_message(msg)
        time.sleep(0.1)

# Start telemetry publishing
if __name__ == "__main__":
    publish_telemetry()
    #listen_for_messages()

def signal_handler(sig, frame):
    print("\nTermiating telemetry publishing...")
    session.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)