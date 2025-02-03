import socketio

# Create a Socket.IO client
sio = socketio.Client()

# Define event handlers
@sio.event
def connect():
    print("Connected to the server!")
    print("=====================================")
    print(f"Namespaces available: {sio.namespaces}")
    print("=====================================")

@sio.event
def disconnect():
    print("Disconnected from the server!")

@sio.on("telemetry_update")
def on_telemetry_update(data):
    pass
    #print("Received telemetry update in /:", data)

@sio.event
def connect_error(data):
    print("Connection failed:", data)

# Define event handlers for the namespace
@sio.on("connect", namespace="/drone/001")
def connect_to_namespace():
    print("Connected to the /drone/001 namespace!")

@sio.on("disconnect", namespace="/drone/001")
def disconnect_from_namespace():
    print("Disconnected from the /drone/001 namespace!")

@sio.on("telemetry_update", namespace="/drone/001")
def on_telemetry_update(data):
    pass
    # print("Received telemetry update in /drone/001:")#), data)
    # print(data["telemetry"]["gps_raw_int"])
    # print(data["telemetry"]["timestamp"])


@sio.on("connect", namespace="/drone/002")
def connect_to_namespace():
    print("Connected to the /drone/002 namespace!")

@sio.on("disconnect", namespace="/drone/002")
def disconnect_from_namespace():
    print("Disconnected from the /drone/002 namespace!")

@sio.on("telemetry_update", namespace="/drone/002")
def on_telemetry_update(data):
    pass
    # print("Received telemetry update in /drone/002:")#), data)
    # print(data["telemetry"]["gps_raw_int"])
    # print(data["telemetry"]["timestamp"])


@sio.on("connect", namespace="/mydrones")
def connect_to_namespace():
    print("Connected to the /mydrones namespace!")

@sio.on("disconnect", namespace="/mydrones")
def disconnect_from_namespace():
    print("Disconnected from the /mydrones namespace!")

@sio.on("heartbeat", namespace="/mydrones")
def on_heartbeat_update(data):
    print("----- Received heartbeat update in /mydrones:")#, data)


@sio.on("connect", namespace="/mydronesstatus")
def connect_to_namespace():
    print("Connected to the /mydronesstatus namespace!")

@sio.on("disconnect", namespace="/mydronesstatus")
def disconnect_from_namespace():
    print("Disconnected from the /mydronesstatus namespace!")

@sio.on("statustext", namespace="/mydronesstatus")
def on_statustext_update(data):
    print("----- Received statustext update in /mydronesstatus:", data)

# Main function to connect to the server
def main():
    try:
        namespace = "/drone/002"
        sio.connect(f"http://localhost:8001", namespaces=["/", namespace, "/mydrones", "/mydronesstatus"], socketio_path="socket.io") #, namespaces=["/", namespace])
        #sio.connect(f"http://localhost:8001")
        print("Socket.IO client connected!")
        print("Available namespaces from server:", sio.namespaces)


        # Force activation of the namespace
        if namespace in sio.namespaces:
            sio.emit("force_activation", data={}, namespace=namespace)
        else:
            print(f"Namespace {namespace} is missing from the client!")
        # Wait for events
        sio.wait()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
