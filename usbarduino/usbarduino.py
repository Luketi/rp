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
    c = c + 1
    if c % 10 == 0:
        syslog.syslog('ARDUINO: ' + l.decode("utf-8") )

    if c % 200 == 0:
        data = urllib.parse.urlencode({'pid' : '3',
                         'bid' : '130',
                         'data0' : 1,
                         'data3' : 'arduino.local.heartbeat',
                         'data4' : 'recv data'
                         })

        content = urllib.request.urlopen(url=url, data=data.encode('utf-8')).read()
        print(content)
        syslog.syslog('Arduino Heartbeat Sent to Server: ' + content.decode("utf-8") )


    if c % 100 == 0:
        data = urllib.parse.urlencode({'pid' : '3',
                         'bid' : '101',
                         'data0' : 1,
                         'data3' : 'arduino.remote.heartbeat',
                         'data4' : l.decode("utf-8")  
                         })

        content = urllib.request.urlopen(url=url, data=data.encode('utf-8')).read()
        print(content)
        syslog.syslog('Arduino Heartbeat Sent to Server: ' + content.decode("utf-8") )

