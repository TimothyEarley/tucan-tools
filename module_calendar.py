#!/usr/bin/env python3

import os
import json
import vv_exporter
from bs4 import BeautifulSoup
from ics import Calendar, Event
import dateparser
from pytz import timezone

current_path = os.path.dirname(os.path.abspath(__file__))
MODULES_JSON = os.path.join(current_path, 'modules.json')
CALENDAR_OUT = os.path.join(current_path, 'module_calendar.ics')

tz = timezone('Europe/Berlin')


def main():
    args = get_args()
    whitelist = args.modules
    calendar = Calendar()
    modules = get_modules()
    for module in modules:
        vv_exporter.walk_modules(module, lambda vv: extract_calendar(vv, calendar, whitelist))
    with open(CALENDAR_OUT, 'w') as f:
        f.writelines(calendar)


def get_modules():
    if not os.path.exists(MODULES_JSON):
        raise (Exception('{} not found. Run vv_exporter first.'.format(MODULES_JSON)))
    with open(MODULES_JSON, 'r') as f:
        return json.load(f)


def extract_calendar(vv, calendar, whitelist):
    title = vv['title']
    # if we have a whitelist, check the title is covered by it
    if whitelist is not None and not any(s.lower() in title.lower() for s in whitelist):
        return vv

    details = vv.get('details')
    if not details:
        return vv

    try:
        appointments = next(x for x in details if x['title'] == "Kurstermine")["details"]
        table = BeautifulSoup(appointments, "html.parser")
        for row in table.find_all('tr', class_=lambda x: x != 'rw-hide'):
            date = row.find(attrs={"name": "appointmentDate"}).get_text()
            time_from = row.find(attrs={"name": "appointmentTimeFrom"}).get_text()
            time_to = row.find(attrs={"name": "appointmentDateTo"}).get_text()
            rooms = row.find(attrs={"name": "appointmentRooms"})
            instructors = row.find(attrs={"name": "appointmentInstructors"}).get_text()

            calendar.events.add(Event(
                name=title,
                begin=dateparser.parse("{} {}".format(date, time_from), languages=['de']).astimezone(tz),
                end=dateparser.parse("{} {}".format(date, time_to), languages=['de']).astimezone(tz),
                location=rooms.get_text() if rooms is not None else "",
                description="Instructors: {}".format(instructors)
            ))
        print("Added {} to calendar".format(title))
    except StopIteration:
        print("No appointments found for {}".format(title))
    return vv


def get_args():
    import argparse
    parser = argparse.ArgumentParser(description='Convert modules to ICalendar format', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-m', '--modules', nargs='+', required=False, help='Modules to use. If none given all are included')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
