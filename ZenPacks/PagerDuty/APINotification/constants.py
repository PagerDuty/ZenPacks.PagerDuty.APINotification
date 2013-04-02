EVENT_API_URI = 'https://events.pagerduty.com/generic/2010-04-15/create_event.json'
ALL_PROPERTIES = ['service_key', 'summary', 'description', 'incident_key', 'details']

from models import enum

EventType = enum(TRIGGER='trigger', ACKNOWLEDGE='acknowledge', RESOLVE='resolve')
Properties = enum(SERVICE_KEY='service_key', SUMMARY='summary', DESCRIPTION='description',
                  INCIDENT_KEY='incident_key', DETAILS='details')

REQUIRED_PROPERTIES = [Properties.SERVICE_KEY, Properties.SUMMARY, Properties.DESCRIPTION, Properties.INCIDENT_KEY]
