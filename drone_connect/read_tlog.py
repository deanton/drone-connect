from pymavlog import MavTLog

filepath = "mav.tlog"
tlog = MavTLog(filepath=filepath)

tlog.parse()

print(tlog.types)

print(tlog._start_timestamp)
print(tlog._end_timestamp)

for type in tlog._parsed_data:
    print(type)
    
    for msg in tlog.get(key=type):
        print(msg)
        

