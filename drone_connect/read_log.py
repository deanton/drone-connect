from pymavlink import mavutil
from pymavlink import DFReader

#log = mavutil.mavlink_connection('mav.tlog')
log = mavutil.mavlink_connection('2024-11-05 14-17-04.tlog')
#log = mavutil.mavlink_connection('2024-11-05 14-17-04.rlog')

while True:
    m = log.recv_msg()
    if m is None:
        break
    print(m)
