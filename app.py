#!/usr/bin/env python3
import os

import aws_cdk as cdk

from localtech_auth.auth_stack import LocaltechAuthStack


app = cdk.App()

# Get hosted zone ID from context or environment
hosted_zone_id = app.node.try_get_context("hosted_zone_id") or os.getenv("HOSTED_ZONE_ID")

LocaltechAuthStack(
    app, 
    "LocaltechAuthStack",
    hosted_zone_id=hosted_zone_id,
    # Use the current CLI configuration for account and region
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'), 
        region=os.getenv('CDK_DEFAULT_REGION')
    ),
)

app.synth()
