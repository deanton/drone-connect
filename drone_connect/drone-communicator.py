import time
from pymavlink import mavutil
from urllib3 import connection
import zenoh
import threading
import json
import signal
import sys
import os

my_name = os.path.basename(__file__)

# Connect to the drone via MAVLink
connection_string = 'udp:127.0.0.1:14550'
drone = mavutil.mavlink_connection(connection_string)

print("Waiting for heartbeat...")
result = drone.wait_heartbeat()
print(f"Heartbeat received: {result}")

# Initialize Zenoh session
session = zenoh.open(zenoh.Config())
name = "002"
stop_event = threading.Event() # Event to signal threads to stop

def telemetry_listener(message_type):
    """
    Thread function to listen for specific MAVLink messages and publish them to Zenoh.
    """
    resource_key = f"myhome/drone/{name}/telemetry/{message_type}"
    print(f"Started telemetry listener for {message_type}")

    while not stop_event.is_set():
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
            #print(f"Published {message_type} to Zenoh: {payload}")
        time.sleep(0.1)

def heartbeat_listener():
    """
    Thread function to listen for MAVLink HEARTBEAT messages and publish them to Zenoh.
    """
    resource_key = f"myhome/drone/{name}/HEARTBEAT"
    print("Started heartbeat listener")

    while not stop_event.is_set():
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
            #print(f"Published HEARTBEAT to Zenoh: {payload}")
        time.sleep(0.1)

def statustext_listener():
    """
    Thread function to listen for MAVLINK STATUSTEXT messages and publish them to Zenoh.
    """

    resource_key = f"myhome/drone/{name}/STATUSTEXT"
    print("Started statustext listener")

    while not stop_event.is_set():
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
            print("------------------------------------------")
            print(f"Published STATUSTEXT to Zenoh: {payload}")
            print("------------------------------------------")
        time.sleep(0.1)

def zenoh_request_listener():
    """
    Zenoh subscriber to handle incoming request for MAVLink data.
    Sends a MAVLink request to the drone and publishes the response to Zenoh.
    """
    request_key = f"myhome/drone/{name}/request"
    response_key = f"myhome/drone/{name}/response"
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

def signal_handler(sig, frame):
    """
    Handle SIGINT (Ctrl+C) for graceful shutdown.
    """
    print("\nTermination telemetry publishing")
    stop_event.set()
    session.close()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Define MAVLINK message types to listen for
    message_types = ["GPS_RAW_INT", "BATTERY_STATUS"]

    # Start telemetry listeners
    threads = start_telemetry_listeners(message_types)

    # Start Zenoh request listener
    zenoh_request_thread = threading.Thread(target=zenoh_request_listener)
    zenoh_request_thread.start()

    for thread in threads:
        thread.join()
    zenoh_request_thread.join()