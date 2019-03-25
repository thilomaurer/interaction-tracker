#!/usr/bin/env python3
import sys
import time

#evts={}
act={}

ofilename="tracker.log"
ofile=open(ofilename,"a")

lastm=-1

def dateFromMinute(m):
    return time.asctime(time.localtime(m*60))

def log_event(t,p):
    global lastm
    #if not t in evts:
    #    evts[t]={}
    #x=evts[t]
    #if p in x:
    #    x[p]+=1
    #else:
    #    x[p]=1
    m=int(t/60)
    if not m in act:
        act[m]=1
        if lastm>=0:
            data=[dateFromMinute(lastm),str(lastm),str(act[lastm])]
            line=" ; ".join(data)+"\n"
            ofile.write(line)
            ofile.flush()
            print(line)
    else:
        act[m]+=1
    lastm=m

for line in sys.stdin:
    if line.startswith("EVENT type "):
        eventtime=int(time.time())
        eventtype=int(line.split(" ")[2])
        log_event(eventtime, eventtype)
