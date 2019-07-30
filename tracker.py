#!/usr/bin/env python3
import sys
import time
import argparse
import datetime
import NetworkManager
from gcalapi import google_calendar_api

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

xinput_event_type = {
     0: "Any",
     1: "DeviceChanged",
     2: "KeyPress",
     3: "KeyRelease",
     4: "ButtonPress",
     5: "ButtonRelease",
     6: "Motion",
     8: "Leave",
     9: "FocusIn",
    10: "FocusOut",
    11: "HierarchyChanged",
    12: "PropertyEvent",
    13: "RawKeyPress",
    14: "RawKeyRelease",
    15: "RawButtonPress",
    16: "RawButtonRelease",
    17: "RawMotion"
}

def get_locations():
    locs = []
    try:
        cons = NetworkManager.NetworkManager.ActiveConnections
    except:
        cons = []
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

class calendarExporter():
    def __init__(self, calname):
        self.api = google_calendar_api()
        self.calname = calname
        self.calendarId = self.api.lookup_calendarId(calname)

    @staticmethod
    def eventTitle(evt):
        xin = evt['xinput']
        keys = xin.get(3,"no")
        clicks = xin.get(4,"no")
        return "{} keys, {} clicks".format(keys, clicks)

    @staticmethod
    def eventLocation(evt):
        loc = evt.get('location',None)
        if loc:
            locstr = ', '.join(loc)
        else:
            locstr = None
        return locstr

    def addEvent(self, start, end, evt):
        startDate = datetime.datetime.fromtimestamp(start*60).astimezone()
        endDate = datetime.datetime.fromtimestamp(end*60).astimezone()
        title = calendarExporter.eventTitle(evt)
        location = calendarExporter.eventLocation(evt)
        print("Create calendar entry {}, at {}, starting {}, ending {}".format(title,location,startDate,endDate))
        try:
            self.api.create_event(self.calendarId,title,startDate,endDate,location)
        except:
            e = sys.exc_info()[0]
            print(e, file=sys.stderr)

class merger:
    def __init__(self, mergegap, calex):
        self.sumevt = {}
        self.windowstart = None
        self.windowend = None
        self.mergegap = mergegap
        self.calex = calex

    @staticmethod
    def accumulate(base,delta):
        for k,v in delta.items():
            if k in base:
                base[k]+=v
            else:
                base[k]=v

    def addEvent(self, evt):
        m = evt['minute']
        if not type(evt) is dict:
            evt = {'xinput':{'0': evt}}
        if not 'xinput' in evt:
            evt = {'xinput':evt}
        if self.windowstart == None:
            self.sumevt=evt
            self.windowstart=m
            self.windowend=m
        elif m > self.windowend + self.mergegap:
            # new date is in new window
            if self.calex:
                self.calex.addEvent(self.windowstart,self.windowend,self.sumevt)
            self.windowstart=m
            self.sumevt=evt
            self.windowend=m
        else:
            # new date is in same window
            self.windowend=m
            if sorted(self.sumevt.get('location',[])) == sorted(evt.get('location',[])):
                merger.accumulate(self.sumevt['xinput'],evt['xinput'])
            else:
                if self.calex:
                    self.calex.addEvent(self.windowstart,self.windowend,self.sumevt)
                self.windowstart=m
                self.sumevt=evt
                self.windowend=m

mergegap = 5
calex = calendarExporter("Thilo's Thinkpad")
merg = merger(mergegap, calex)

def dateFromMinute(m):
    return time.asctime(time.localtime(m*60))

def write_log(lastm):
    data=[dateFromMinute(lastm),str(evts[lastm])]
    line=" ; ".join(data)+"\n"
    ofile.write(line)
    ofile.flush()
    print(line)

def log_event(t,p):
    global lastm
    m=int(t/60)
    if not m in evts:
        evts[m]={'minute': m, 'xinput': {0:0}, 'location': get_locations()}
        if lastm>=0:
            write_log(lastm)
            merg.addEvent(evts[lastm])
    lastm=m
    x=evts[m]['xinput']
    if not p in x:
        x[p]=0
    x[p]+=1
    x[0]+=1

def main():
    for line in sys.stdin:
        if line.startswith("EVENT type "):
            eventtime=int(time.time())
            eventtype=int(line.split(" ")[2])
            if not eventtype in args.ignore_event_type:
                log_event(eventtime, eventtype)

main()

