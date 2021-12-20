#!/usr/bin/env python3

# Copyright The Linux Foundation and each contributor to LFX.
# SPDX-License-Identifier: MIT

import datetime
import json
import os
import re
from typing import Any, Dict, Optional

import requests
from criticality_score import run


class TokenManager:
    """
    Token manager wraps the business logic of fetching, caching, expiring and providing access to the access token.
    """

    def __init__(self):
        self.token = None
        self.expires = None

    def __str__(self):
        return f'TokenManager token {self.token[0:10]}... expires {self.expires}'

    def invalidate_token(self):
        self.token = None
        self.expires = datetime.date(year=1972, month=4, day=19)

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


token_manager = TokenManager()


def validate_input(event_body: Dict[str, Any]) -> bool:
    fn = 'validate_input'

    valid = True
    # Check the input - make sure we have everything
    if 'STAGE' not in os.environ:
        print('missing STAGE environment variable')
        valid = False
    if 'AUTH0_PLATFORM_URL' not in os.environ:
        print('missing AUTH0_PLATFORM_URL environment variable')
        valid = False
    if 'AUTH0_PLATFORM_CLIENT_ID' not in os.environ:
        print('missing AUTH0_PLATFORM_CLIENT_ID environment variable')
        valid = False
    if 'AUTH0_PLATFORM_CLIENT_SECRET' not in os.environ:
        print('missing AUTH0_PLATFORM_CLIENT_SECRET environment variable')
        valid = False
    if 'AUTH0_PLATFORM_AUDIENCE' not in os.environ:
        print('missing AUTH0_PLATFORM_AUDIENCE environment variable')
        valid = False
    if 'github_auth_token' not in event_body:
        print(f'{fn} - unable to generate criticality score report - missing github_auth_token from event data')
        valid = False
    if event_body['github_auth_token'] == '':
        print(f'{fn} - unable to generate criticality score report - github_auth_token value is empty')
        valid = False
    if 'repository_url' not in event_body:
        print(f'{fn} - unable to generate criticality score report - missing target repository_url from event data')
        valid = False
    if event_body['repository_url'] == '':
        print(f'{fn} - unable to generate criticality score report - repository_url value is empty')
        valid = False
    if 'repository_id' not in event_body:
        print(f'{fn} - unable to generate criticality score report - missing target repository_url from event data')
        valid = False
    if event_body['repository_id'] == '':
        print(f'{fn} - unable to generate criticality score report - repository_id value is empty')
        valid = False
    if 'project_id' not in event_body:
        print(f'{fn} - unable to generate criticality score report - missing project_id from event data')
        valid = False
    if event_body['project_id'] == '':
        print(f'{fn} - unable to generate criticality score report - project_id value is empty')
        valid = False
    if 'project_sfid' not in event_body:
        print(f'{fn} - unable to generate criticality score report - missing project_sfid from event data')
        valid = False
    if event_body['project_sfid'] == '':
        print(f'{fn} - unable to generate criticality score report - project_sfid value is empty')
        valid = False

    return valid


def send_data(project_id: str, project_sfid: str, repository_id: str, score_data: Dict[str, Any], stage: str) -> None:
    fn = 'send_data'
    if stage == 'dev':
        url = f'https://api-gw.dev.platform.linuxfoundation.org/security-service/v2/{project_sfid}/ossf-scores'
    elif stage == 'staging':
        url = f'https://api-gw.staging.platform.linuxfoundation.org/security-service/v2/{project_sfid}/ossf-scores'
    elif stage == 'prod':
        url = f'https://api-gw.platform.linuxfoundation.org/security-service/v2/{project_sfid}/ossf-scores'
    else:
        print(f'invalid stage value {stage} - expecting one one: [dev, staging, prod]')
        return

    payload = {
        'project_id': project_id,
        'project_sfid': project_sfid,
        'repository_id': repository_id,
        'language': score_data.get('language', ''),
        'created_since': score_data.get('created_since', 0),
        'updated_since': score_data.get('updated_since', 0),
        'contributor_count': score_data.get('contributor_count', 0),
        'org_count': score_data.get('org_count', 0),
        'commit_frequency': score_data.get('commit_frequency', 0.0),
        'recent_releases_count': score_data.get('recent_releases_count', 0),
        'updated_issues_count': score_data.get('updated_issues_count', 0),
        'closed_issues_count': score_data.get('closed_issues_count', 0),
        'comment_frequency': score_data.get('comment_frequency', 0.0),
        'dependents_count': score_data.get('dependents_count', 0),
        'criticality_score': score_data.get('criticality_score', 0.0),
    }

    headers = {
        'Authorization': f'bearer {token_manager.get_access_token()}',
        'Content-type': 'application/json',
        'Accept': 'application/json',
    }

    try:
        print(f'Sending POST request to: {url} with payload: {payload}')
        r = requests.post(url, json=payload, headers=headers)
        r.raise_for_status()
        if r.status_code < 200 or r.status_code > 299:
            print(f'{fn} - invalid response status code received: {r.status_code} - error: {r.text}')
        else:
            print(f'{fn} - successfully send add repository ossf scores data...')
    except requests.exceptions.HTTPError as err:
        print(f'{fn} - invalid response from add repository ossf scores endpoint, error: {err}')
    return None


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    start_time = datetime.datetime.now()
    fn = 'lambda_handler'
    print(f'{fn} - received event: {event} with context: {context}')

    if 'body' not in event:
        print(f'{fn} - received event with no body - unable to process message')
        return {}

    event_body = json.loads(event['body'])
    print(f'{fn} - event {type(event_body)}: {event_body}')

    # Check the input - make sure we have everything
    if not validate_input(event_body):
        return {}

    # Set this value in the environment
    os.environ["GITHUB_AUTH_TOKEN"] = event_body['github_auth_token']

    stage = os.environ['STAGE']

    # extract our repository from the event data
    url = event_body['repository_url']
    url = re.sub(r'^https?://', '', url, flags=re.IGNORECASE)

    project_id = event_body['project_id']
    project_sfid = event_body['project_sfid']
    project_name = event_body['project_name']
    repository_id = event_body['repository_id']
    print(f'{fn} - {stage} - processing repository: {url}')

    try:
        repo = run.get_repository(url)
        output = run.get_repository_stats(repo, [])
        print(f'{fn} - {stage} - received data: {json.dumps(output, indent=2)}')
        send_data(project_id, project_sfid, repository_id, output, stage)
    except Exception as ex:
        print(f'{fn} - problem fetching repository details or stats '
              f'for project: {project_name} '
              f'with sfid: {project_sfid}. '
              f'error is: {ex}')

    print(f'Finished processing - duration: {datetime.datetime.now() - start_time}')


def main():
    # invoked from the command line

    if 'GITHUB_AUTH_TOKEN' not in os.environ:
        print('missing GITHUB_AUTH_TOKEN environment variable')

    # Event data for the lambda - below are test/junk values
    # event = {
    #     # Consider adding additional meta-data for this message
    #     # See: https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html
    #     "body": {
    #         "id": "38e2ef0e-1983-4444-aaaa-222222222222",
    #         "type": "ossf_scan",
    #         "version": "v1",
    #         "project_id": "38e2ef0e-1983-4c92-a9f0-98255cd61af1",
    #         "project_sfid": "a092M000000000000000000000",
    #         "project_name": "Foo",
    #         "created_date_time": 0,
    #         "repository_id": "435f5013-4406-4fcc-954c-zzzzzzzzzzzzzzz",
    #         "repository_url": "https://github.com/communitybridge/easycla",
    #         "github_auth_token": 'ghs_XYZ......',
    #     }
    # }
    event2 = {
        'body': '{"id":"testtest-5ce6-4558-8d6b-abad9e82a7fd","type":"ossf_scan","version":"v1","project_sfid":"a092M00001IV7AiQAL","project_id":"testtest-1983-4c92-a9f0-98255cd61af1","project_name":"EasyCLA","created_datetime":1634753930,"repository_id":"testtest-1bd8-430e-953e-0f5f0a369d03","repository_url":"https://github.com/communitybridge/docs","github_auth_token":"ghs_XXXXXXXXXXXXXX"}'}

    # Context data for the lambda
    # see: https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    context = {
        "function_name": "lfx-security-ossf-scanner"
    }
    lambda_handler(event2, context)


if __name__ == "__main__":
    main()
