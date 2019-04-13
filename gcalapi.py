#!/usr/bin/env python3

from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def first(items, pred):
    return next((i for i in items if pred(i)), None)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.events','https://www.googleapis.com/auth/calendar.readonly']

class google_calendar_api:

    def __init__(self):
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'google-calendar-api-credentials.json', SCOPES)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('calendar', 'v3', credentials=creds)

    def list_upcoming(self):
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        events_result = self.service.events().list(calendarId='primary', timeMin=now,
                                            maxResults=10, singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])

    def lookup_calendarId(self, calname):
        cals = self.service.calendarList().list().execute().get('items',[])
        #shortcals = map(lambda c: {'id':c['id'], 'name':c['summary']},cals)
        calendarId = first(cals, lambda c: c['summary']==calname)['id']
        return calendarId

    def create_event(self, calendarId, eventTitle, startDate, endDate, location):
        eventBody = {
            "summary": eventTitle,
            "start": { # The (inclusive) start time of the event. For a recurring event, this is the start time of the first instance.
                #"date": "A String", # The date, in the format "yyyy-mm-dd", if this is an all-day event.
                #"timeZone": "A String", # The time zone in which the time is specified. (Formatted as an IANA Time Zone Database name, e.g. "Europe/Zurich".) For recurring events this field is required and specifies the time zone in which the recurrence is expanded. For single events this field is optional and indicates a custom time zone for the event start/end.
                "dateTime": startDate.isoformat('T') # The time, as a combined date-time value (formatted according to RFC3339). A time zone offset is required unless a time zone is explicitly specified in timeZone.
            },
            "end": { # The (exclusive) end time of the event. For a recurring event, this is the end time of the first instance.
                #"date": "A String", # The date, in the format "yyyy-mm-dd", if this is an all-day event.
                #"timeZone": "A String", # The time zone in which the time is specified. (Formatted as an IANA Time Zone Database name, e.g. "Europe/Zurich".) For recurring events this field is required and specifies the time zone in which the recurrence is expanded. For single events this field is optional and indicates a custom time zone for the event start/end.
                "dateTime": endDate.isoformat('T') # The time, as a combined date-time value (formatted according to RFC3339). A time zone offset is required unless a time zone is explicitly specified in timeZone.
            },
            "location": location,
            "transparency": "transparent"

        }
        insert_result = self.service.events().insert(calendarId=calendarId, body=eventBody).execute()
        if insert_result.get('status', None) != 'confirmed':
            print("Error creating event {}".format(eventTitle))
        return insert_result

if __name__ == '__main__':
    api = google_calendar_api()
    calname = "Thilo's Thinkpad"
    calendarId = api.lookup_calendarId(calname)
    startDate = datetime.datetime.now(datetime.timezone.utc).astimezone()
    endDate = startDate + datetime.timedelta(minutes=111)
    eventTitle = "my class test"
    api.create_event(calendarId, eventTitle,startDate,endDate)

