#!/usr/bin/env python3

# Copyright The Linux Foundation and each contributor to CommunityBridge.
# SPDX-License-Identifier: MIT
import json
import os
from datetime import datetime

from criticality_score import run


def lambda_handler(event, context):
    start_time = datetime.now()
    fn = 'lambda_handler'
    context.log(f'received event: {event}')

    # Check the input - make sure we have everything
    if 'github_auth_token' not in event:
        context.log(f'unable to generate criticality score report - missing github_auth_token from event data')
        return
    if 'repository' not in event:
        context.log(f'unable to generate criticality score report - missing target repository from event data')
        return

    # Set this value in the environment
    os.environ["GITHUB_AUTH_TOKEN"] = event['github_auth_token']

    # extract our repository from the event data
    url = event["repository"]
    context.log(f'{fn} - processing repository: {url}')

    repo = run.get_repository(url)
    output = run.get_repository_stats(repo, [])
    print(json.dumps(output, indent=4))

    # TODO: add to repository_statistics table
    # How to add to the DB?
    # 1. Direct DB Insert
    # 2. Send AWS SNS Message, but this seems overkill, not necessary
    # 3. Send API request via HTTPS, then API will add to the DB for me...
    context.log(f'Finished processing - duration: {datetime.now() - start_time}')


def main():
    # invoked from the command line

    if 'GITHUB_AUTH_TOKEN' not in os.environ:
        print(f'missing GITHUB_AUTH_TOKEN environment variable')

    # Event data for the lambda
    event = {
        "repository": "github.com/communitybridge/easycla-contributor-console",
        "github_auth_token": os.environ['GITHUB_AUTH_TOKEN']
    }

    # Context data for the lambda
    # see: https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    context = {
        "function_name": "lfx-security-ossf-scanner"
    }
    lambda_handler(event, context)


if __name__ == "__main__":
    main()
