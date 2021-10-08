#!/usr/bin/env python3

# Copyright The Linux Foundation and each contributor to CommunityBridge.
# SPDX-License-Identifier: MIT
import json
import os
from datetime import datetime
from typing import Any, Dict

from criticality_score import run


def validate_input(event: Dict[str, Any]) -> bool:
    fn = 'validate_input'

    # Check the input - make sure we have everything
    if 'STAGE' not in os.environ:
        print(f'missing STAGE environment variable')
    if 'github_auth_token' not in event:
        print(f'{fn} - unable to generate criticality score report - missing github_auth_token from event data')
        return False
    if 'repository' not in event:
        print(f'{fn} - unable to generate criticality score report - missing target repository from event data')
        return False
    if 'repository_id' not in event:
        print(f'{fn} - unable to generate criticality score report - missing target repository_url from event data')
        return False

    return True


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    start_time = datetime.now()
    fn = 'lambda_handler'
    print(f'{fn} - received event: {event}')

    # Check the input - make sure we have everything
    if not validate_input(event):
        return {}

    # Set this value in the environment
    os.environ["GITHUB_AUTH_TOKEN"] = event['github_auth_token']

    stage = os.environ['STAGE']

    # extract our repository from the event data
    url = event["repository"]
    print(f'{fn} - {stage} - processing repository: {url}')

    repo = run.get_repository(url)
    output = run.get_repository_stats(repo, [])
    print(json.dumps(output, indent=2))

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
        "stage": os.environ['STAGE'],
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
