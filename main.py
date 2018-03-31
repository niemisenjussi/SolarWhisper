import serial

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=5)
#ser.write("AT\r")
while(True):
    response =  ser.readline()
    print response


ser.close()

