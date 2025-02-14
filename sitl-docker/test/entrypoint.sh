#!/bin/bash
set -e

# Default values
VEHICLE_TYPE=${VEHICLE_TYPE:-copter} # Vehicle type (copter, plane, rover)
INSTANCE_ID=${INSTANCE_ID:-"drone1"} # String-based instance ID
ZENOH_PREFIX=${ZENOH_PREFIX:-"myhome/drone"}
TCP_PORT=${TCP_PORT:-5760} # MAVLink exposed TCP Port
UDP_PORT=${UDP_PORT:-14551} # MAVLink UDP Port

echo "Starting SITL instance '$INSTANCE_ID' as $VEHICLE_TYPE..."

cd /home/ardupilot/ardupilot

# Determine correct SITL binary
if [ "$VEHICLE_TYPE" = "copter" ]; then
    SITL_BINARY="ArduCopter"
elif [ "$VEHICLE_TYPE" = "plane" ]; then
    SITL_BINARY="ArduPlane"
elif [ "$VEHICLE_TYPE" = "rover" ]; then
    SITL_BINARY="ArduRover"
else
    echo "Unkown vehicle type: $VEHICLE_TYPE"
    exit 1
fi

# Start SITL in the background
#screen -dmS sitl_$INSTANCE_ID ./Tools/autotest/sim_vehicle.py -v $SITL_BINARY -f gazebo-iris --out=udp:127.0.0.1:$UDP_PORT --out=tcp:0.0.0.0:$TCP_PORT
# Start SITL in the background using tmux
echo "tmux new-session -d -s sitl_$INSTANCE_ID ./Tools/autotest/sim_vehicle.py -v $SITL_BINARY -w --speedup 1 -D --no-mavproxy --no-extra-ports --moddebug=3 -f gazebo-iris --out=udp:127.0.0.1:$UDP_PORT --out=tcp:0.0.0.0:$TCP_PORT"
#tmux new-session -d -s sitl_$INSTANCE_ID ./Tools/autotest/sim_vehicle.py -v $SITL_BINARY -w --speedup 1 -D --no-mavproxy --no-extra-ports --moddebug=3 -f gazebo-iris --out=udp:127.0.0.1:$UDP_PORT --out=tcp:0.0.0.0:$TCP_PORT
su -c "tmux new-session -d -s sitl_$INSTANCE_ID ./Tools/autotest/sim_vehicle.py -v $SITL_BINARY -w --speedup 1 -D --no-mavproxy --no-extra-ports --moddebug=3 -f gazebo-iris --out=udp:127.0.0.1:$UDP_PORT --out=tcp:0.0.0.0:$TCP_PORT" -s /bin/bash ardupilot

# /ardupilot/Tools/autotest/sim_vehicle.py --vehicle ${VEHICLE} -I${INSTANCE} --custom-location=${LAT},${LON},${ALT},${DIR} -w --frame ${MODEL} --no-rebuild --no-mavproxy --speedup ${SPEEDUP}

echo "Waiting for SITL to initialize..."
sleep 10

# Check if SITL started properly
#if ! pgrep -f "arducopter" && ! pgrep -f "arduplane" && ! pgrep -f "ardurover"; then
if ! pgrep -f "arducopter|arduplane|ardurover"; then
    echo "SITL failed to start! Keeping container running for debugging..."
    tail -f /dev/null
    exit 1
fi

echo "Starting MAVProxy..."
tmux new-session -d -s mavproxy_$INSTANCE_ID mavproxy.py --master=tcp:127.0.0.1:$TCP_PORT --out=udp:127.0.0.1:$UDP_PORT #--console --map

echo "MAVProxy started. Monitoring MAVLink..."

# # Keep container running
# tail -f /dev/null

# echo "Starting MAVProxy..."
# screen -dmS mavproxy mavproxy.py --master=tcp:127.0.0.1:$TCP_PORT --out=udp:127.0.0.1:$UDP_PORT

# sleep 10

echo "Starting MAVLink-Zenoh script for $VEHICLE_TYPE instance '$INSTANCE_ID'..."

# Restart Python script on failure
while true; do
    python3 /home/ardupilot/drone-communicator.py --instance "$INSTANCE_ID" --zenoh-prefix "$ZENOH_PREFIX"
    echo "MAVLink-Zenoh script crashed! Restarting..."
    sleep 2 # Prevent infinit fast restarts
done