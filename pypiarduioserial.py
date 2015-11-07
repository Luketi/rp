import serial
ser = serial.Serial('/dev/ttyUSB0', 9600)

print('test')

while 1 :
    print(ser.readline())
