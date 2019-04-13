#!/usr/bin/env python3
import sys
import ast
import time
import json
import datetime
import functools
import argparse
from gcalapi import google_calendar_api

parser = argparse.ArgumentParser(description='HID Interaction Tracker - Window Merger')
parser.add_argument('-i','--ifilename', metavar='ofilename', type=str, default="interaction.log", help='output filename')
args = parser.parse_args()

ifile = open(args.ifilename,"r")

mergegap=5

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


api = google_calendar_api()
calname = "Thilo's Thinkpad"
calendarId = api.lookup_calendarId(calname)

def eventTitle(evt):
    xin=evt['xinput']
    keys = xin.get(3,"no")
    clicks = xin.get(4,"no")
    return "{} keys, {} clicks".format(keys, clicks)

def eventLocation(evt):
    loc=evt.get('location',None)
    if loc:
        locstr=', '.join(loc)
    else:
        locstr=None
    return locstr

def addEvent(start,end,evt):
    startDate = datetime.datetime.fromtimestamp(start*60).astimezone()
    endDate = datetime.datetime.fromtimestamp(end*60).astimezone()
    title = eventTitle(evt)
    location = eventLocation(evt)
    print(startDate,endDate,location,title)
    api.create_event(calendarId,title,startDate,endDate,location)

def dateFromMinute(m):
    return time.asctime(time.localtime(m*60))

def addWindow(start,end):
    minutes=end-start+1
    hours=int(minutes/60)
    minutes=minutes-hours*60
    print(dateFromMinute(start), " to ", dateFromMinute(end), "{0: >2}h {1: >2}m".format(hours,minutes))
    startDate = datetime.datetime.now(datetime.timezone.utc).astimezone()
    endDate = startDate + datetime.timedelta(minutes=111)
   
def accumulate(base,delta):
    for k,v in delta.items():
        if k in base:
            base[k]+=v
        else:
            base[k]=v

sumevt={}
windowstart=None
windowend=None

for line in ifile:
    fields = line.split(";")
    m=int(fields[1])
    evt = ast.literal_eval(fields[2].strip())
    if not type(evt) is dict:
        evt = {'xinput':{'0': evt}}
    if not 'xinput' in evt:
        evt = {'xinput':evt}
    if windowstart == None:
        sumevt=evt
        windowstart=m
        windowend=m
    elif m > windowend + mergegap:
        # new date is in new window
        addEvent(windowstart,windowend,sumevt)
        windowstart=m
        sumevt=evt
        windowend=m
    else:
        # new date is in same window
        windowend=m
        if sorted(sumevt.get('location',[])) == sorted(evt.get('location',[])):
            accumulate(sumevt['xinput'],evt['xinput'])
        else:
            addEvent(windowstart,windowend,sumevt)
            windowstart=m
            sumevt=evt
            windowend=m



#add final window if complete
m = int(time.time())/60
if m > windowend + mergegap:
    addEvent(windowstart,windowend,sumevt)
