#!/usr/bin/env python3

import datetime
# Copyright The Linux Foundation and each contributor to CommunityBridge.
# SPDX-License-Identifier: MIT
import json
import os
from datetime import datetime
from typing import Optional

import requests


class TokenManager:
    def __init__(self):
        self.token = None
        self.expires = None

    def __str__(self):
        return f'TokenManager token {self.token[0:10]}... expires {self.expires}'

    def invalidate_token(self):
        self.token = None
        self.expires = datetime.date(1972, 4, 19)

    def get_access_token(self) -> Optional[str]:
        fn = 'get_access_token'

        if self.token is not None and self.expires is not None and self.expires < datetime.datetime.utcnow():
            print(f'{fn} - using cached access_token: {self.token[0:10]}...')
            return self.token

        auth0_url = os.environ['AUTH0_PLATFORM_URL']
        platform_client_id = os.environ['AUTH0_PLATFORM_CLIENT_ID']
        platform_client_secret = os.environ['AUTH0_PLATFORM_CLIENT_SECRET']
        platform_audience = os.environ['AUTH0_PLATFORM_AUDIENCE']

        auth0_payload = {
            'grant_type': 'client_credentials',
            'client_id': platform_client_id,
            'client_secret': platform_client_secret,
            'audience': platform_audience
        }

        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'accept': 'application/json'
        }

        try:
            r = requests.post(auth0_url, data=auth0_payload, headers=headers)
            r.raise_for_status()
            json_data = json.loads(r.text)
            self.token = json_data["access_token"]
            self.expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=json_data["expires_in"])
            print(f'{fn} - successfully obtained new access_token: {self.token[0:10]}, expires on {self.expires}...')
            return self.token
        except requests.exceptions.HTTPError as err:
            print(f'{fn} - could not get auth token, error: {err}')
            return None
