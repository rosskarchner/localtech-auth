#!/usr/bin/env python3
import os

import aws_cdk as cdk

from localtech_auth.auth_stack import LocaltechAuthStack


app = cdk.App()
LocaltechAuthStack(app, "LocaltechAuthStack",
    # Use the current CLI configuration for account and region
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
    )

app.synth()
