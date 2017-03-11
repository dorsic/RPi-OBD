import obd
import time
import sys
from datetime import datetime
from gps3.agps3threaded import AGPS3mechanism

#  OBDII
obd.logger.setLevel(obd.logging.DEBUG) # enables all debug information
sensors = ['SPEED', 'RPM', 'THROTTLE_POS', 'ENGINE_LOAD', 'COOLANT_TEMP', 'RUN_TIME', 'DISTANCE_W_MIL', 'FUEL_LEVEL', 'BAROMETRIC_PRESSURE', 'CATALYST_TEMP_B1S1', 'CONTROL_MODULE_VOLTAGE', 'ABSOLUTE_LOAD', 'AMBIANT_AIR_TEMP', 'OIL_TEMP', 'FUEL_RATE', 'THROTTLE_ACTUATOR']

#  GPS 
agps_thread = AGPS3mechanism()  # Instantiate AGPS3 Mechanisms
agps_thread.stream_data()  # From localhost (), or other hosts, by example, (host='gps.ddns.net')
agps_thread.run_thread()  # Throttle time to sleep after an empty lookup, default '()' 0.2 two tenths of a second


class OBD_Recorder():
    def __init__(self, sensors, logdir = './', port = None):
        self.connection = None
        self.port = port
        localtime = time.localtime(time.time()) 
        filename = logdir + "car-"+str(localtime[0])+"-"+str(localtime[1])+"-"+str(localtime[2])+"-"+str(localtime[3])+"-"+str(localtime[4])+"-"+str(localtime[5])+".log"
        self.log_file = open(filename, "w", 128)
        self.log_file.write('[TIMESTAMP, SPEED, RPM, THROTTLE_POS, ENGINE_LOAD, COOLANT_TEMP, RUN_TIME, DISTANCE_W_MIL, FUEL_LEVEL, BAROMETRIC_PRESSURE, CATALYST_TEMP_B1S1, CONTROL_MODULE_VOLTAGE, ABSOLUTE_LOAD, AMBIANT_AIR_TEMP, OIL_TEMP, FUEL_RATE, THROTTLE_ACTUATOR, GEAR]\n')
        
        self.sensors = sensors
        self.gear_ratios = [34/13, 39/21, 36/23, 27/20, 26/21, 25/22]

    def connect(self):
    	if (self.port == None):
        	self.connection = obd.OBD() # auto-connects to USB or RF port
        else:
        	self.connection = obd.OBD(self.port)
        return self.connection.is_connected()

    def isConnected(self):
        if (self.connection == None):
            return False
        return self.connection.is_connected()

    def calculateGear(self, rpm, speed):
        if speed == "" or speed == 0:
            return 0
        if rpm == "" or rpm == 0:
            return 0

        rps = rpm/60
        mps = (speed*1.609*1000)/3600
        
        primary_gear = 85/46 #street triple
        final_drive  = 47/16
        
        tyre_circumference = 1.978 #meters
# audi winter 205/60/R16 circumreference = 2047mm  (489rev/km)
# audi summer 225/50/R17 circumreference = 2063mm  (485rev/km)
# audi alt summer 225/45/R17 circumreference = 1991mm  (502rev/km)

        current_gear_ratio = (rps*tyre_circumference)/(mps*primary_gear*final_drive)
        
        print current_gear_ratio
        gear = min((abs(current_gear_ratio - i), i) for i in self.gear_ratios)[1] 
        return gear

    def recordData(self):
        cnt = 0
        while True:
            result = []
            speedKPH = agps_thread.data_stream.speed*1.851999999984 if type(agps_thread.data_stream.speed) == float else agps_thread.data_stream.speed
            gpsData = [agps_thread.data_stream.time, agps_thread.data_stream.lon, agps_thread.data_stream.lat, agps_thread.data_stream.alt, speedKPH, agps_thread.data_stream.track]

            result.append(str(datetime.now()))
            if (self.isConnected()):
                for c in self.sensors:
                    cmd = obd.commands[c]   # select an ODB command (sensor)
                    response = self.connection.query(cmd)    # send the command, and parse the response
                    if (not response.is_null()):
                        result.append(response.value)
                    else:
                        result.append('')
                result.append(self.calculateGear(result[1], result[0]))
            else:
                result.append(['n/a','n/a','n/a','n/a','n/a','n/a','n/a','n/a','n/a','n/a','n/a','n/a','n/a','n/a','n/a','n/a'])

            result.append(gpsData)
            self.log_file.write(str(result)+'\n')
            print(str(result))
            cnt = cnt+1
            time.sleep(1)


logDir = None
port = None
if (len(sys.argv) > 1):
	logDir = str(sys.argv[1])
if (len(sys.argv) > 2):
	port = str(sys.argv[2])

o = OBD_Recorder(sensors, logDir, port)
o.connect()
if not o.isConnected():
    print "Not connected"
o.recordData()

