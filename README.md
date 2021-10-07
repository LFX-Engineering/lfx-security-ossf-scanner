# LFX Security OSSF Scanner

This tool wraps the OSSF score tool as an AWS lambda so that we can generate the report for each active project in LFX
Security.

## Deployment

```bash
yarn deploy:dev
```

## Command Line Testing

```bash
# First: Log into your AWS account for the appropriate environment
# Second: invoke using the desired payload, adjust the target repository and provide a GitHub authorization token value
aws --region us-east-2 lambda invoke \
  --function-name lfx-securitry-ossf-scanner-dev-ossf-scanner \
  --cli-binary-format raw-in-base64-out \
  --payload '{"repository":"github.com/communitybridge/easycla", "github_auth_token":"ghs_XXXX..."}' \
  out.txt
```

## References

- [Open Source Project Criticality Score - GitHub](https://github.com/ossf/criticality_score)
- [LFX Security API](https://github.com/LF-Engineering/lfx-security)
- [LFX Security Console](https://github.com/LF-Engineering/vulnerability-detection)

## License

Copyright The Linux Foundation and each contributor to LFX.

This project’s source code is licensed under the MIT License. A copy of the license is available in LICENSE.

The project includes source code from keycloak, which is licensed under the Apache License, version 2.0 \(Apache-2.0\), a copy of which is available in LICENSE-keycloak.

This project’s documentation is licensed under the Creative Commons Attribution 4.0 International License \(CC-BY-4.0\). A copy of the license is available in LICENSE-docs.
