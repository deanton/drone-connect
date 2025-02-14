import zenoh
import time

# # Zenoh session initialization
# session = zenoh.open(zenoh.Config())
# print(session)

# Create a Zenoh session with explicit connection to ZenohD
config = zenoh.Config()
config.insert_json5("connect/endpoints", "[\"tcp/127.0.0.1:7447\"]")  
session = zenoh.open(config)

# Open Zenoh session
#session = zenoh.open(zenoh.Config())

print("🔍 Connected to Zenoh at tcp://127.0.0.1:7447")

# Subscribe to ALL messages
SUBSCRIPTION_KEY = "**" # Wildcard to capture all messages

def listener(sample):
    """
    Callback function to handle incoming Zenoh messages. 
    """
    message = sample.payload.to_bytes().decode("utf-8")
    print(f"[{time.strftime('%H:%M:%S')}] Received {sample.key_expr} -> {message}")

print(f"Subscribing to: {SUBSCRIPTION_KEY}")
session.declare_subscriber(SUBSCRIPTION_KEY, listener)

# Keep script running to receive messages
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n Exiting...")
    session.close()