#!/usr/bin/env python3
import sys
import ast
import csv
import yaml
import time
import json
import pprint
import copy
import datetime
import functools
import argparse
from termcolor import colored
from tabulate import tabulate
import locale


pp = pprint.PrettyPrinter(indent=4)

parser = argparse.ArgumentParser(description='HID Interaction Tracker - Window Merger')
parser.add_argument('-i','--ifilename',type=str, default="interaction.log")
parser.add_argument('-g','--geofilename', action='append', default=[])
parser.add_argument('-x','--extrafiles', action='append', default=[])
parser.add_argument('-d','--days', action='store_true', default=False)
parser.add_argument('-v','--verbose', action='store_true', default=False)
parser.add_argument('range', type=str, nargs='*')
args = parser.parse_args()

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

def eventTitle(evt):
    xin=evt['xinput']
    keys = xin.get(3,"no")
    clicks = xin.get(4,"no")
    return "{} keys, {} clicks".format(keys, clicks)

def eventLocation(evt):
    loc=evt.get('location',None)
    if loc:
        locstr=', '.join(map(lambda l: 'wifi:'+l,loc))
    else:
        locstr=None
    return locstr

events = []

def addEvent(start,end,evt):
    startDate = datetime.datetime.fromtimestamp(start*60).astimezone()
    endDate = datetime.datetime.fromtimestamp(end*60).astimezone()
    title = eventTitle(evt)
    location = eventLocation(evt)
    events.append({"start":startDate,"end":endDate,"location":location})
    #print(startDate,endDate,location,title)

def dateFromMinute(m):
    return time.asctime(time.localtime(m*60))

#def addWindow(start,end):
#    minutes=end-start+1
#    hours=int(minutes/60)
#    minutes=minutes-hours*60
#    print(dateFromMinute(start), " to ", dateFromMinute(end), "{0: >2}h {1: >2}m".format(hours,minutes))
#    startDate = datetime.datetime.now(datetime.timezone.utc).astimezone()
#    endDate = startDate + datetime.timedelta(minutes=111)
   
def accumulate(base,delta):
    for k,v in delta.items():
        if k in base:
            base[k]+=v
        else:
            base[k]=v

sumevt={}
windowstart=None
windowend=None

with open(args.ifilename,"r") as ifile:
    for line in ifile:
        fields = line.split(";")
        try:
            m=int(fields[1])
            evt = ast.literal_eval(fields[2].strip())
        except:
            evt = ast.literal_eval(fields[1].strip())
            m = evt['minute']
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


def loadholidays():
    state = 'BW'
    filenames = [
        "holidays/feiertage-2014.json",
        "holidays/feiertage-2015.json",
        "holidays/feiertage-2016.json",
        "holidays/feiertage-2017.json",
        "holidays/feiertage-2018.json",
        "holidays/feiertage-2019.json",
        "holidays/feiertage-2020.json"
    ]    
    dd=[]
    for filename in filenames:
        with open(filename, 'r') as f:
            d = json.loads(f.read())
        dates=map(lambda f: d[state][f[1]]['datum'],enumerate(d[state]))
        dates=map(lambda d: datetime.datetime.strptime(d, '%Y-%m-%d').date(), dates)
        dd.extend(list(dates))
    return dd

holidays = loadholidays()

def loadvacation(filename):
    days=[]
    daylabels=[]
    with open(filename, 'r') as f:
        v = yaml.safe_load(f.read())
    for a in v['vacation']:
        start = datetime.datetime.strptime(a['start'], '%d.%m.%y').date()
        end   = datetime.datetime.strptime(a['end'], '%d.%m.%y').date()
        dates = daterange(start,end)
        #for d in dates:
        #    daylabels[
        days.append(dates)
    days = [item for sublist in days for item in sublist]
    return days

def loadsickdays(filename):
    days=[]
    daylabels=[]
    with open(filename, 'r') as f:
        v = yaml.safe_load(f.read())
    for a in v['sickdays']:
        start = datetime.datetime.strptime(a['start'], '%d.%m.%y').date()
        end   = datetime.datetime.strptime(a['end'], '%d.%m.%y').date()
        dates = daterange(start,end)
        #for d in dates:
        #    daylabels[
        days.append(dates)
    days = [item for sublist in days for item in sublist]
    return days

def loadgeofency(filename):
    loc = locale.getlocale(locale.LC_NUMERIC)
    locale.setlocale(locale.LC_NUMERIC, 'de_DE')
    dd = []
    with open(filename, 'r') as f:
        cr = csv.reader(f, delimiter=';', quotechar='"')
        header = None
        for row in cr:
            row=list(row)
            if header==None:
                header=row
            else:
                d = {}
                d["location"] = row[0]
                d["index"] = int(row[1])
                d["start"] = datetime.datetime.strptime(row[2]+" "+row[3],'%d.%m.%y %H:%M:%S').astimezone()
                d["end"] = datetime.datetime.strptime(row[4]+" "+row[5],'%d.%m.%y %H:%M:%S').astimezone()
                d["hours"] = locale.atof(row[6])
                d["hhmmss"] = row[7]
                d["comment"] = row[8]
                d["latitude"] = locale.atof(row[9])
                d["longitude"] = locale.atof(row[10])
                dd.append(d)
    locale.setlocale(locale.LC_NUMERIC, loc)
    return(dd)

def loadextra(filename):
    with open(filename, 'r') as f:
        v = yaml.safe_load(f.read())
    dd = []
    for a in v['extra']:
        d = {}
        d["location"] = a["location"]
        d["start"] = datetime.datetime.strptime(a["start"],'%d.%m.%y %H:%M:%S').astimezone()
        d["end"] = datetime.datetime.strptime(a["end"],'%d.%m.%y %H:%M:%S').astimezone()
        d["comment"] = a.get("comment", None)
        d["latitude"] = a.get("latitiude",None)
        d["longitude"] = a.get("longitude",None)
        dd.append(d)
    return dd

#print(json.dumps(events,indent=4))


from datetime import timedelta, date

def daterange(date1, date2):
    for n in range(int ((date2 - date1).days)+1):
        yield date1 + timedelta(n)

def isholiday(d):
    return d in holidays

def isvacation(d):
    days=[
        daterange(date(2019,7,29),date(2019,8,2)),
        daterange(date(2019,4,5),date(2019,5,5)),
        daterange(date(2019,9,5),date(2019,10,5))
    ]
    days_flat = [item for sublist in days for item in sublist]
    return d in vacation

def issickday(d):
    days=[date(2019,7,19)]
    return d in sickdays


def earliertime(d1,d2):
    if d1 == None:
        return d2
    if d2 == None:
        return d1
    if d1 > d2:
        return d2
    else:
        return d1

def latertime(d1,d2):
    if d1 == None:
        return d2
    if d2 == None:
        return d1
    if d1 < d2:
        return d2
    else:
        return d1


def mergeevents(dd):
    nd = []
    cur = None
    for i,d in enumerate(dd):
        if cur == None:
            cur = copy.deepcopy(d)
        else:
            if d['end'] < cur['end']:
                None
                #pp.pprint("contained:")
                #pp.pprint(d)
            elif d['start'] < cur['end']:
                #pp.pprint("extend:")
                #pp.pprint(d)
                cur['end'] = d['end']
                cur['location'] += ', '+d['location']
            else:
                nd.append(cur)
                cur = copy.deepcopy(d)
    if cur != None:
        nd.append(cur)
    #pp.pprint(nd)
    return nd


def isweekend(d):
    wd = d.weekday()
    return(wd==5 or wd==6)


def daytype(d):
    if isweekend(d):
        return "weekend"
    if isvacation(d):
        return "vacation"
    if issickday(d):
        return "sickday"
    if isholiday(d):
        return "holiday"
    return ""


args.geofilename=list(set(args.geofilename))
geoevents = []
for gf in args.geofilename:
    geoevents.extend(loadgeofency(gf))


def loadextraevents(files):
    files=list(set(files))
    e = []
    for f in files:
        e.extend(loadextra(f))
    return e

extraevents = loadextraevents(args.extrafiles)
vacation = loadvacation("vacation.yaml")
sickdays = loadsickdays("sickdays.yaml")

geolocations = [ 'IBM', 'IBM 2', 'IBM 3', 'Büro', 'Kantine', "Le Meridien Al Khobar", "Aramco Headquarters"]

geoworkevents = list(filter(lambda e: e.get('location',"") in geolocations, geoevents))

first_event_date = min([geoworkevents[0]['start'].date() ,events[0]['start'].date()])
last_event_date = max([geoworkevents[len(geoworkevents)-1]['end'].date() ,events[len(events)-1]['end'].date()])

def addgeolabel(e):
    e['location']='geo:'+e['location']
    return(e)

missing_events = []


def calcgaps(events):
    gg = []
    for i,e in enumerate(events):
        if i+1<len(events):
            g = {
                'start': e['end'],
                'end': events[i+1]['start']
            }
            gg.append(g)
    return gg

def getday(d):
    wd = d.weekday()
    if (wd == 0):
        weektime = 0
    dayevents = list(filter(lambda e: (e['start'].date() == d) and ('IBM' in (e.get('location',"") or "")),events))
    dayevents2 = list(filter(lambda e: (e['start'].date() == d),geoworkevents))
    dayevents2 = map(addgeolabel,dayevents2)
    dayevents3 = list(filter(lambda e: (e['start'].date() == d),extraevents))
    dayevents.extend(dayevents2)
    dayevents.extend(dayevents3)
    dayevents.sort(key=lambda e:e['start'].timestamp())
    allevents = dayevents
    dayevents = mergeevents(dayevents)
    workedtime = sum(map(lambda e: e['end'].timestamp()-e['start'].timestamp(),dayevents)) / 60
    gapevents = calcgaps(dayevents)
    daygaptime = sum(map(lambda e: e['end'].timestamp()-e['start'].timestamp(),gapevents)) / 60
    noworkday = isweekend(d) or isholiday(d) or isvacation(d) or issickday(d)
    if noworkday:
        goaltime = 0
    elif workedtime < 6*60:
        goaltime = 38/5*60
    elif daygaptime > 50:
        goaltime = 38/5*60
    else:
        goaltime = 38/5*60 + 50
    overtime = workedtime - goaltime
    strange = workedtime == 0 and goaltime != 0
    otstr = coloredtime(overtime)
    if strange:
        #overtime = 0
        missing_events.append(d)
        #otstr = colored('?',"yellow")
    return {
        'date': d,
        'daytype': daytype(d),
        'overtime': overtime,
        'gaptime': daygaptime,
        'overtimestr': otstr,
        'noworkday': noworkday,
        'events': dayevents,
        'allevents': allevents,
        'strange': strange
    }

def coloredtime(ot,color=None):
    otstr = "{:+.2f}".format(ot/60) if ot != 0 else ""
    if color==None:
        if ot<-120:
            otstr = colored(otstr,'red')
        if ot>120:
            otstr = colored(otstr,'green') 
    else:
            otstr = colored(otstr,color) 
    return otstr

def compile_dayview(start, end):
    weektime=0
    totaltime=0
    details = args.verbose
    tabs=[]
    for d in daterange(start, end):
        g = getday(d)
        wd = d.weekday()
        if (wd == 0):
            weektime = 0
        ot = g['overtime']
        weektime += ot
        totaltime += ot
        otstr = coloredtime(ot)
        wtstr = coloredtime(weektime)
        tabs.append([g['date'].strftime("%Y-%m-%d %a"), g['daytype'], otstr, "{:.0f} m".format(g['gaptime']), wtstr if wd==6 else None])
        if details == True:
            #for de in g['events']:
            #    tabs.append(['',de['start'].time(),de['end'].time(), de['location'], de.get('comment',"")])
            for de in g['allevents']:
                dt = de['end'].timestamp()-de['start'].timestamp()
                diffdays = (de['end'].date()-de['start'].date()).days
                diffdays = " {:+} day{}".format(diffdays,"s" if diffdays > 1 else "") if diffdays > 0 else ""
                tabs.append(['',de['start'].time(),str(de['end'].time()) + str(diffdays), "{:.0f} m".format(dt/60), de['location'], de.get('comment',"")])
    headers = ["date","daytype","overtime","pausetime","weeksum",""]
    return (headers, tabs)

def compile_weekview(start, end):
    weektime=0
    totaltime=0
    details = True
    tabs=[]
    tab = [''] * start.weekday()
    for d in daterange(start, end):
        g = getday(d)
        wd = d.weekday()
        if (wd == 0):
            weektime = 0
        ot = g['overtime']
        weektime += ot
        totaltime += ot
        p = g['date'].strftime("%d") + " " + g['overtimestr']
        tab.append(p)
        if wd == 6 or d==end:
            week = d.isocalendar()[1]
            month = d.strftime("%b")
            year = d.year
            tab = tab + [""] * (7-len(tab))
            tabs.append([year,week,month]+tab+[coloredtime(weektime),coloredtime(totaltime)])
            tab = []
    headers=["year","week","month","Mon","Tue","Wed","Thu","Fri","Sat","Sun","Overtime","Accumulated"]
    return((headers,tabs))

if len(args.range)==0:
    start = first_event_date
    end = last_event_date
else:
    days = args.range[0].split('-')
    if len(days)>0:
        start = datetime.datetime.strptime(days[0], '%d.%m.%y').date()
    if len(days)>1:
        if days[1]=='':
            end = last_event_date
        elif  days[1]=='now':
            end = datetime.date.today()
        else:
            end = datetime.datetime.strptime(days[1], '%d.%m.%y').date()
    else:
        end = start

if args.days:
    headers, tabs = compile_dayview(start,end)
    print(tabulate(tabs,headers=headers))
else:
    headers, tabs = compile_weekview(start, end)
    print(tabulate(tabs,headers=headers))
       
if len(missing_events)>0:
    print("work-days with no work registered:", ", ".join(map(lambda d:str(d),missing_events)))
    
