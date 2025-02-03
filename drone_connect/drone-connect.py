import time
from pymavlink import mavutil
import paho.mqtt.client as mqtt

# Connect to the drone via MAVLink 
#connection_string = 'tcp:127.0.0.1:5760'
connection_string = 'udp:127.0.0.1:14550'
drone = mavutil.mavlink_connection(connection_string)

# Initialize MQTT client
#mqtt_client = mqtt.Client()
#mqtt_broker = "broker.hivemq.com"
#mqtt_client.connect(mqtt_broker, 1883, 80)


print("waiting for heartbeat")
drone.wait_heartbeat()
print("passed wait heartbeat")

# Publish MAVLink telemetry to MQTT
def publish_telemetry():
    while True:
        
        print("requesting GPS_RAW_INT")
        msg = drone.recv_match(type='GPS_RAW_INT', blocking=True)
        print("got msg")
        if msg:
            gps_data = {
                'lat': msg.lat / 1e7, # Convert to decimal degrees
                'lon': msg.lon / 1e7,
                'alt': msg.alt / 1000.0 # convert to meter
            }

            #mqtt_client.publish("/drone/telemetry/gps", str(gps_data))
            print(f"Published GPS data to MQTT: {gps_data}")
        
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
    #publish_telemetry()
    listen_for_messages()