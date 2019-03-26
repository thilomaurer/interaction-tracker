#!/usr/bin/env python3
import sys
import time

evts={}

ofilename="tracker.log"
ofile=open(ofilename,"a")

lastm=-1

def dateFromMinute(m):
    return time.asctime(time.localtime(m*60))


def write(lastm):
    data=[dateFromMinute(lastm),str(lastm),str(evts[lastm])]
    line=" ; ".join(data)+"\n"
    ofile.write(line)
    ofile.flush()
    print(line)

def log_event(t,p):
    global lastm
    m=int(t/60)
    if not m in evts:
        evts[m]={"any":0}
        if lastm>=0:
            write(lastm)
    lastm=m
    x=evts[m]

    if not p in x:
        x[p]=0
    x[p]+=1
    x["any"]+=1

for line in sys.stdin:
    if line.startswith("EVENT type "):
        eventtime=int(time.time())
        eventtype=int(line.split(" ")[2])
        log_event(eventtime, eventtype)
