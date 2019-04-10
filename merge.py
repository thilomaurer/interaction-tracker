#!/usr/bin/env python3
import sys
import time
import argparse

parser = argparse.ArgumentParser(description='HID Interaction Tracker - Window Merger')
parser.add_argument('-i','--ifilename', metavar='ofilename', type=str, default="interaction.log", help='output filename')
args = parser.parse_args()

ifile = open(args.ifilename,"r")

mergegap=5

def dateFromMinute(m):
    return time.asctime(time.localtime(m*60))

def addWindow(start,end):
    minutes=end-start+1
    hours=int(minutes/60)
    minutes=minutes-hours*60
    print(dateFromMinute(start), " to ", dateFromMinute(end), "{0: >2}h {1: >2}m".format(hours,minutes))
            
windowstart=None
windowend=None

for line in ifile:
    fields = line.split(";")
    m=int(fields[1])
    if windowstart == None:
        windowstart=m
        windowend=m
    elif m > windowend + mergegap:
        # new date is in new window
        addWindow(windowstart,windowend)
        windowstart=m
        windowend=m
    else:
        # new date is in same window
        windowend=m


#add final incomplete window
addWindow(windowstart,windowend)
