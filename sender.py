from __future__ import division
from subprocess import PIPE, Popen
import os
import urllib
import urllib.request
import logging
import cgi
import re
import time 

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
                         'bid' : '0',
                         'data0' : tmp,
                         'data1' : cpu,
                         'data2' : dsk[3],
                         'data6' : mem[2]
                         })

content = urllib.request.urlopen(url=url, data=data.encode('utf-8')).read()

print(content)
