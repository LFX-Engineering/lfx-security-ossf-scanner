#!/usr/bin/env python3

# Copyright The Linux Foundation and each contributor to CommunityBridge.
# SPDX-License-Identifier: MIT
import json

from criticality_score import run


def lambda_handler(event, context):
    fn = context["function_name"]
    url = event["repository"]
    print(f'{fn} - processing repository: {url}')
    repo = run.get_repository(url)
    output = run.get_repository_stats(repo, [])
    print(json.dumps(output, indent=4))


def main():
    # invoked from the command line

    # Event data for the lambda
    event = {
        "repository": "github.com/communitybridge/easycla"
    }

    # Context data for the lambda
    # see: https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    context = {
        "function_name": "lfx-security-ossf-scanner"
    }
    lambda_handler(event, context)


if __name__ == "__main__":
    main()
