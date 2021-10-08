#!/usr/bin/env python3

# Copyright The Linux Foundation and each contributor to CommunityBridge.
# SPDX-License-Identifier: MIT

import json
import os
from datetime import datetime
from typing import Any, Dict

import requests
from criticality_score import run


def validate_input(event: Dict[str, Any]) -> bool:
    fn = 'validate_input'

    valid = True
    # Check the input - make sure we have everything
    if 'STAGE' not in os.environ:
        print(f'missing STAGE environment variable')
        valid = False
    if 'AUTH0_PLATFORM_URL' not in os.environ:
        print(f'missing AUTH0_PLATFORM_URL environment variable')
        valid = False
    if 'AUTH0_PLATFORM_CLIENT_ID' not in os.environ:
        print(f'missing AUTH0_PLATFORM_CLIENT_ID environment variable')
        valid = False
    if 'AUTH0_PLATFORM_CLIENT_SECRET' not in os.environ:
        print(f'missing AUTH0_PLATFORM_CLIENT_SECRET environment variable')
        valid = False
    if 'AUTH0_PLATFORM_AUDIENCE' not in os.environ:
        print(f'missing AUTH0_PLATFORM_AUDIENCE environment variable')
        valid = False
    if 'github_auth_token' not in event:
        print(f'{fn} - unable to generate criticality score report - missing github_auth_token from event data')
        valid = False
    if 'repository' not in event:
        print(f'{fn} - unable to generate criticality score report - missing target repository from event data')
        valid = False
    if 'repository_id' not in event:
        print(f'{fn} - unable to generate criticality score report - missing target repository_url from event data')
        valid = False
    if 'project_id' not in event:
        print(f'{fn} - unable to generate criticality score report - missing project_id from event data')
        valid = False
    if 'project_sfid' not in event:
        print(f'{fn} - unable to generate criticality score report - missing project_sfid from event data')
        valid = False

    return valid


def get_access_token():
    fn = 'get_access_token'

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
        print(f'{fn} - successfully obtained access_token: {json_data["access_token"][0:10]}...')
        return json_data["access_token"]
    except requests.exceptions.HTTPError as err:
        print(f'{fn} - could not get auth token, error: {err}')
        return None


def send_data(project_id: str, project_sfid: str, score_data: Dict[str, Any], stage: str) -> None:
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
        'Authorization': f'bearer {get_access_token()}',
        'accept': 'application/json'
    }

    try:
        r = requests.post(url, data=payload, headers=headers)
        r.raise_for_status()
        print(f'{fn} - successfully send add repository ossf scores data...')
    except requests.exceptions.HTTPError as err:
        print(f'{fn} - invalid response from add repository ossf scores endpoint, error: {err}')
    return None


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    start_time = datetime.now()
    fn = 'lambda_handler'
    print(f'{fn} - received event: {event} with context: {context}')

    # Check the input - make sure we have everything
    if not validate_input(event):
        return {}

    # Set this value in the environment
    os.environ["GITHUB_AUTH_TOKEN"] = event['github_auth_token']

    stage = os.environ['STAGE']

    # extract our repository from the event data
    url = event['repository']
    project_id = event['project_id']
    project_sfid = event['project_sfid']
    print(f'{fn} - {stage} - processing repository: {url}')

    repo = run.get_repository(url)
    output = run.get_repository_stats(repo, [])
    print(f'{fn} - {stage} - received data: {json.dumps(output, indent=2)}')
    send_data(project_id, project_sfid, output, stage)

    # TODO: add to repository_statistics table
    # How to add to the DB?
    # 1. Direct DB Insert
    # 2. Send AWS SNS Message, but this seems overkill, not necessary
    # 3. Send API request via HTTPS, then API will add to the DB for me...
    print(f'Finished processing - duration: {datetime.now() - start_time}')


def main():
    # invoked from the command line

    if 'GITHUB_AUTH_TOKEN' not in os.environ:
        print(f'missing GITHUB_AUTH_TOKEN environment variable')

    # Event data for the lambda
    event = {
        "project_id": "",
        "project_sfid": "",
        "repository_id": "435f5013-4406-4fcc-954c-d21a6a9f289b",
        "repository": "github.com/communitybridge/easycla",
        "github_auth_token": os.environ['GITHUB_AUTH_TOKEN'],
    }

    # Context data for the lambda
    # see: https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    context = {
        "function_name": "lfx-security-ossf-scanner"
    }
    lambda_handler(event, context)


if __name__ == "__main__":
    main()
