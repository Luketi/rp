from __future__ import absolute_import, division, print_function, unicode_literals
from subprocess import PIPE, Popen
import os
import urllib
import urllib.request
import logging
import cgi
import re
import time
import pigpio
import serial
import logging.handlers
import syslog

syslog.openlog( 'usbarduino', 0, syslog.LOG_LOCAL4 )
syslog.syslog( 'USB Arduino Serial listener started' )


url = 'http://botmeshed.appspot.com/update'
data = urllib.parse.urlencode({'pid' : '2',
                         'bid' : '3',
                         'data0' : 1,
                         'data3' : 'usbarduino.daemon.boot'
                         })

content = urllib.request.urlopen(url=url, data=data.encode('utf-8')).read()
print(content)
syslog.syslog('Response from server: ' + content.decode("utf-8") ) 


ser = serial.Serial('/dev/ttyUSB0', 9600)

c = 0
while 1 :
    l = ser.readline()
    print(l)
    msg = l.decode("utf-8")
    parts = msg.split()
    
# DATA PACKET
# bytes: [protocol version][board id][seq id][app id][recipient board id][value byte 0][value byte 1] ...

    if len(parts) < 6:
        continue

    ver = int(parts[0])
    bid = int(parts[1])
    seq = int(parts[2])
    app = int(parts[3])
    rec = int(parts[4])

    if ver > 10:
        continue

    if app == 4 and len(parts) > 6:
        lv = int(parts[5]) + int(parts[6]) * 256
        data = urllib.parse.urlencode({'pid' : app,
                         'bid' : bid,
                         'data0' : lv
                         })
                         
    elif app == 5 and len(parts) > 8:
        t = (int(parts[5]) + int(parts[6]) * 256) / 100
        h = (int(parts[7]) + int(parts[8]) * 256) / 100
        
        data = urllib.parse.urlencode({'pid' : app,
                         'bid' : bid,
                         'data0' : t,
                         'data1' : h,
                         })
    content = urllib.request.urlopen(url=url, data=data.encode('utf-8')).read()
    print(content)
    syslog.syslog('Arduino Event Sent to Server: ' + content.decode("utf-8") )

    c = c + 1
    
    if c % 1000 == 0:
        data = urllib.parse.urlencode({'pid' : '3',
                         'bid' : '3',
                         'data0' : 1,
                         'data3' : 'arduino.local.heartbeat',
                         'data4' : 'recv data'
                         })

        content = urllib.request.urlopen(url=url, data=data.encode('utf-8')).read()
        print(content)
        syslog.syslog('Arduino Heartbeat Sent to Server: ' + content.decode("utf-8") )

    
