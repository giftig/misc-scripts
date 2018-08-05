#!/usr/bin/env python2.7

import calendar
import datetime
import os
import sys

import requests


class NotificationPusher(object):
    def __init__(self, api_key, user_key, api_url):
        self.api_key = api_key
        self.user_key = user_key
        self.api_url = api_url

    def send_message(self, title, message, timestamp=None, priority=0):
        data = {
            'token': API_KEY,
            'user': USER_KEY,
            'title': title,
            'message': message,
            'timestamp': timestamp,
            'priority': priority
        }

        resp = requests.post(API_URL, data=data)

        status = resp.status_code
        if status < 200 or status > 299:
            print 'FAILURE: ', status, resp.json()
            return False

        return True


if __name__ == '__main__':
    API_KEY = os.environ['PUSHOVER_TOKEN']
    USER_KEY = os.environ['PUSHOVER_USER']
    API_URL = 'https://api.pushover.net/1/messages.json'

    pusher = NotificationPusher(API_KEY, USER_KEY, API_URL)
    success = pusher.send_message(
        sys.argv[1],
        sys.argv[2],
        calendar.timegm(datetime.datetime.now().utctimetuple())
    )
    sys.exit(0 if success else 1)
