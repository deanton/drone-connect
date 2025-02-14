import time
import argparse
from pymavlink import mavutil
import zenoh
import threading
import json
import signal
import sys
import os

# Parse command-line arguments
parser = argparse.ArgumentParser(description="MAVLink to Zenoh bridge")
parser.add_argument("--instance", type=str, required=True, help="Unique instance ID for this drone (UUID or name)")
parser.add_argument("--zenoh-prefix", type=str, required=True, help="Zenoh topic prefix")
args = parser.parse_args()

INSTANCE_ID = args.instance
ZENOH_PREFIX = args.zenoh_prefix

print(f"Starting MAVLink-Zenoh bridge for instance: {INSTANCE_ID}")
print(f"Zenoh topic prefix: {ZENOH_PREFIX}")

# Set up termination handling
stop_event = threading.Event() 

def signal_handler(sig, frame):
    """
    Handle SIGINT (Ctrl+C) for graceful shutdown.
    """
    print("\nTermination signal received. Stopping services...")
    stop_event.set()
    session.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

my_name = os.path.basename(__file__)

# Connect to the drone via MAVLink
MAVLINK_PORT = 'udp:127.0.0.1:14551'
#MAVLINK_PORT = 'udp:0.0.0.0:14551'  # Listen on any IP


drone = None

def connect_mavlink():
    global drone
    while drone is None:
        try:
            print(f"Connecting to MAVLink on {MAVLINK_PORT}...")
            drone = mavutil.mavlink_connection(MAVLINK_PORT)
            #drone = mavutil.mavlink_connection(MAVLINK_PORT, source_system=1, source_component=1)
            
            print("Waiting for heartbeat...")
            result = drone.wait_heartbeat()
            print(f"Heartbeat received: {result}. MAVLink connection established.")
        except Exception as e:
            print(f"Failed to connect to MAVLink: {e}. Retrying in 5 seconds...")
            time.sleep(5)

connect_mavlink()

# Initialize Zenoh session
session = zenoh.open(zenoh.Config())

def telemetry_listener(message_type):
    """
    Thread function to listen for specific MAVLink messages and publish them to Zenoh.
    """
    resource_key = f"myhome/drone/{INSTANCE_ID}/telemetry/{message_type}"
    print(f"Started telemetry listener for {message_type}")

    while not stop_event.is_set():
        try:
            msg = drone.recv_match(type=message_type, blocking=True, timeout=1)
            if msg:
                timestamp = time.time_ns()
                message = msg.to_dict()
                payload = json.dumps({
                    "timestamp": timestamp,
                    "message_type": message_type,
                    "message": message,
                })
                session.put(resource_key, payload)
                print(f"Sending telemetry at {resource_key}: {payload}")
        except Exception as e:
            print(f"Error receiving {message_type}: {e}")
            time.sleep(1) # Prevent fast looping on errors

def heartbeat_listener():
    """
    Thread function to listen for MAVLink HEARTBEAT messages and publish them to Zenoh.
    """
    resource_key = f"myhome/drone/{INSTANCE_ID}/HEARTBEAT"
    print("Started heartbeat listener")

    while not stop_event.is_set():
        try:
            msg = drone.recv_match(type="HEARTBEAT", blocking=True, timeout=1)
            if msg:
                timestamp = time.time_ns()
                message = msg.to_dict()
                payload = json.dumps({
                    "timestamp": timestamp,
                    "message_type": "HEARTBEAT",
                    "message": message,
                })

                session.put(resource_key, payload)
                print(f"Sending heardbeat at {resource_key}: {payload}")
        except Exception as e:
            print(f"Error receiving HEARTBEAT: {e}")
            time.sleep(1)

def statustext_listener():
    """
    Thread function to listen for MAVLINK STATUSTEXT messages and publish them to Zenoh.
    """

    resource_key = f"myhome/drone/{INSTANCE_ID}/STATUSTEXT"
    print("Started statustext listener")

    while not stop_event.is_set():
        try:
            msg = drone.recv_match(type="STATUSTEXT", blocking=True, timeout=1)
            if msg: 
                timestamp = time.time_ns()
                message = msg.to_dict()
                payload = json.dumps({
                    "timestamp": timestamp,
                    "message_type": "STATUSTEXT",
                    "message": message,
                })
            
                session.put(resource_key, payload)
                print(f"Sending status at {resource_key}: {payload}")
        except Exception as e:
            print(f"Error receiving STATUSTEXT: {e}")
            time.sleep(1)

def zenoh_request_listener():
    """
    Zenoh subscriber to handle incoming request for MAVLink data.
    Sends a MAVLink request to the drone and publishes the response to Zenoh.
    """
    request_key = f"myhome/drone/{INSTANCE_ID}/request"
    response_key = f"myhome/drone/{INSTANCE_ID}/response"
    print(f"Started Zenoh request listener on {request_key}")

    def handle_request(sample):
        try:
            request = json.loads(sample.payload.decode("utf-8"))
            message_type = request.get("message_type")
            print(f"Received Zenoh request for {message_type}")

            # send a Mavlink request
            drone.mav.command_long_send(
                drone.target_system,
                drone.target_component,
                mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE,
                0,
                mavutil.mavlink.message_names[message_type],
                0, 0, 0, 0, 0, 0,
            )

            # Wait for the respone
            response =drone.recv_match(type=message_type, blocking=True, timeout=5)
            if response:
                timestamp = time.time_ns()
                message = response.to_dict()
                payload = json.dumps({
                    "timestamp": timestamp,
                    "message_type": message_type,
                    "message": message,
                })

                session.py(response_key, payload)
                print(f"Published response to Zenoh: {payload}")
            else:
                print(f"No response received for {message_type}")
        except Exception as e:
            print(f"Error handling Zenoh request: {e}")

    session.declare_subscriber(request_key, handle_request)

def start_telemetry_listeners(message_types):
    """
    Start a thread for each specified MAVLink message type.
    """
    threads = []

    # Start telemetry listeners for specific message types
    for message_type in message_types:
        thread = threading.Thread(target=telemetry_listener, args=(message_type,))
        thread.start()
        threads.append(thread)

    # Start the heartbeat listener
    heartbeat_thread = threading.Thread(target=heartbeat_listener)
    heartbeat_thread.start()
    threads.append(heartbeat_thread)

    # Start the statustext listener
    statustext_thread = threading.Thread(target=statustext_listener)
    statustext_thread.start()
    threads.append(statustext_thread)

    return threads

if __name__ == "__main__":
    # Define MAVLINK message types to listen for
    message_types = ["SYS_STATUS", "BATTERY_STATUS", "ATTITUDE", "GLOBAL_POSITION_INT", "VFR_HUD", "ALTITUDE"]

    # Start telemetry listeners
    threads = start_telemetry_listeners(message_types)

    # Start Zenoh request listener
    zenoh_request_thread = threading.Thread(target=zenoh_request_listener)
    zenoh_request_thread.start()

    for thread in threads:
        thread.join()
    zenoh_request_thread.join()