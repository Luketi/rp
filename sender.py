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

class DHT11(object):
    """
    The DHT11 class is a stripped version of the DHT22 sensor code by joan2937.
    You can find the initial implementation here:
    - https://github.com/srounet/pigpio/tree/master/EXAMPLES/Python/DHT22_AM2302_SENSOR

    example code:
    >>> pi = pigpio.pi()
    >>> sensor = DHT11(pi, 4) # 4 is the data GPIO pin connected to your sensor
    >>> for response in sensor:
    ....    print("Temperature: {}".format(response['temperature']))
    ....    print("Humidity: {}".format(response['humidity']))
    """

    def __init__(self, pi, gpio):
        """
        pi (pigpio): an instance of pigpio
        gpio (int): gpio pin number
        """
        self.pi = pi
        self.gpio = gpio
        self.high_tick = 0
        self.bit = 40
        self.temperature = 0
        self.humidity = 0
        self.either_edge_cb = None
        self.setup()

    def setup(self):
        """
        Clears the internal gpio pull-up/down resistor.
        Kills any watchdogs.
        """
        self.pi.set_pull_up_down(self.gpio, pigpio.PUD_OFF)
        self.pi.set_watchdog(self.gpio, 0)
        self.register_callbacks()

    def register_callbacks(self):
        """
        Monitors RISING_EDGE changes using callback.
        """
        self.either_edge_cb = self.pi.callback(
            self.gpio,
            pigpio.EITHER_EDGE,
            self.either_edge_callback
        )

    def either_edge_callback(self, gpio, level, tick):
        """
        Either Edge callbacks, called each time the gpio edge changes.
        Accumulate the 40 data bits from the dht11 sensor.
        """
        level_handlers = {
            pigpio.FALLING_EDGE: self._edge_FALL,
            pigpio.RISING_EDGE: self._edge_RISE,
            pigpio.EITHER_EDGE: self._edge_EITHER
        }
        handler = level_handlers[level]
        diff = pigpio.tickDiff(self.high_tick, tick)
        handler(tick, diff)

    def _edge_RISE(self, tick, diff):
        """
        Handle Rise signal.
        """
        val = 0
        if diff >= 50:
            val = 1
        if diff >= 200: # Bad bit?
            self.checksum = 256 # Force bad checksum

        if self.bit >= 40: # Message complete
            self.bit = 40
        elif self.bit >= 32: # In checksum byte
            self.checksum = (self.checksum << 1) + val
            if self.bit == 39:
                # 40th bit received
                self.pi.set_watchdog(self.gpio, 0)
                total = self.humidity + self.temperature
                # is checksum ok ?
                if not (total & 255) == self.checksum:
                    raise
        elif 16 <= self.bit < 24: # in temperature byte
            self.temperature = (self.temperature << 1) + val
        elif 0 <= self.bit < 8: # in humidity byte
            self.humidity = (self.humidity << 1) + val
        else: # skip header bits
            pass
        self.bit += 1

    def _edge_FALL(self, tick, diff):
        """
        Handle Fall signal.
        """
        self.high_tick = tick
        if diff <= 250000:
            return
        self.bit = -2
        self.checksum = 0
        self.temperature = 0
        self.humidity = 0

    def _edge_EITHER(self, tick, diff):
        """
        Handle Either signal.
        """
        self.pi.set_watchdog(self.gpio, 0)

    def read(self):
        """
        Start reading over DHT11 sensor.
        """
        self.pi.write(self.gpio, pigpio.LOW)
        time.sleep(0.017) # 17 ms
        self.pi.set_mode(self.gpio, pigpio.INPUT)
        self.pi.set_watchdog(self.gpio, 200)
        time.sleep(0.2)

    def close(self):
        """
        Stop reading sensor, remove callbacks.
        """
        self.pi.set_watchdog(self.gpio, 0)
        if self.either_edge_cb:
            self.either_edge_cb.cancel()
            self.either_edge_cb = None

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def __next__(self):
        """
        Call the read method and return temperature and humidity informations.
        """
        self.read()
        response =  {
            'humidity': self.humidity,
            'temperature': self.temperature
        }
        return response


# Return CPU temperature as a character string                                      
def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n",""))

# Return RAM information (unit=kb) in a list                                        
# Index 0: total RAM                                                                
# Index 1: used RAM                                                                 
# Index 2: free RAM                                                                 
def getRAMinfo():
    p = os.popen('free')
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i==2:
            return(line.split()[1:4])

# Return % of CPU used by user as a character string                                
def getCPUuse():
    return(str(os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip(\
)))

# Return information about disk space as a list (unit included)                     
# Index 0: total disk space                                                         
# Index 1: used disk space                                                          
# Index 2: remaining disk space                                                     
# Index 3: percentage of disk used                                                  
def getDiskSpace():
    p = os.popen("df -h /")
    i = 0
    while 1:
        i = i +1
        line = p.readline()
        if i==2:
            return(line.split()[1:5])

tmp = getCPUtemperature()
cpu = getCPUuse()
mem = getRAMinfo()
dsk = getDiskSpace()     
     
print(tmp)
print(cpu)
print(mem)
print(dsk)
           
 
url = 'http://botmeshed.appspot.com/update'
data = urllib.parse.urlencode({'pid' : '0',
                         'bid' : '1',
                         'data0' : tmp,
                         'data1' : cpu,
                         'data2' : dsk[3].replace('%', ''),
                         'data6' : mem[2]
                         })

content = urllib.request.urlopen(url=url, data=data.encode('utf-8')).read()

print(content)


pi = pigpio.pi()
sensor = DHT11(pi, 4)

temp = 0
hum = 0
i = 0

for d in sensor:
    #d = sensor
    print("temperature: {}".format(d['temperature'] * 9 / 5 + 32))
    print("humidity: {}".format(d['humidity']))
    temp = d['temperature'] * 9 / 5 + 32
    hum = d['humidity']
    time.sleep(1)
    i = i + 1
    if i > 20:
        break

sensor.close()


url = 'http://botmeshed.appspot.com/update'
data = urllib.parse.urlencode({'pid' : '1',
                         'bid' : '1',
                         'data0' : temp,
                         'data1' : hum,
                         'data2' : 0,
                         'data6' : 0
                         })

content = urllib.request.urlopen(url=url, data=data.encode('utf-8')).read()

print(content)

