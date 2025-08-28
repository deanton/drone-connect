import asyncio
import socketio

# Enable logs to see connect/handshake details
sio = socketio.AsyncClient(logger=True, engineio_logger=True)

@sio.event
async def connect():
    print("Connected to / (root)")

@sio.on("read", namespace="/haress-platform-metrics-teltonika")
async def teltonika_read(data):
    print("[TEL] read:", data)

@sio.on("read", namespace="/haress-platform-metrics-skycharge")
async def skycharge_read(data):
    print("[SKY] read:", data)

async def main():
    await sio.connect(
        "http://localhost:8001",
        namespaces=[
            "/haress-platform-metrics-teltonika",
            "/haress-platform-metrics-skycharge",
        ],
        transports=["websocket"],           # fine; still needs aiohttp for handshake
        # socketio_path="/socket.io",       # uncomment if your server uses a custom path
    )
    await sio.wait()

asyncio.run(main())
