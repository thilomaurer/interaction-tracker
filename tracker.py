#!/usr/bin/env python3
import sys
import time
import argparse
import NetworkManager

evts={}

parser = argparse.ArgumentParser(description='HID Interaction Tracker')
parser.add_argument('--ignore-event-type', type=int, nargs='*', help='list of xinput event types to igonre')
parser.add_argument('-o','--ofilename', metavar='ofilename', type=str, default="interaction.log", help='output filename')
args = parser.parse_args()

ofile=open(args.ofilename,"a")

lastm=-1

locations = {
        'Home': {
            'wifi': ['Familie Maurer'],
        },
        'IBM': {
            'wifi': ['IBM'],
            'vpn': ['IBM SAS']
        }
}

def get_locations():
    locs = []
    cons = NetworkManager.NetworkManager.ActiveConnections
    for con in cons:
        for loc,v in locations.items():
            if con.Type == "802-11-wireless":
                wifi = v.get('wifi',[])
                if con.Id in wifi:
                    locs.append(loc)
            if con.Type == "vpn":
                wifi = v.get('vpn',[])
                if con.Id in wifi:
                    locs.append(loc)
    return locs


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

        evts[m]={'xinput': {0:0}, 'location': get_locations()}
        if lastm>=0:
            write(lastm)
    lastm=m
    x=evts[m]['xinput']

    if not p in x:
        x[p]=0
    x[p]+=1
    x[0]+=1

for line in sys.stdin:
    if line.startswith("EVENT type "):
        eventtime=int(time.time())
        eventtype=int(line.split(" ")[2])
        if not eventtype in args.ignore_event_type:
            log_event(eventtime, eventtype)
