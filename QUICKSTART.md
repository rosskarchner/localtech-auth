# Quick Start Guide

Get up and running with Localtech Auth in 5 minutes!

## Prerequisites

- AWS Account with admin access
- AWS CLI configured (`aws configure`)
- Node.js and npm (for CDK CLI)
- Python 3.12+ installed
- Route53 hosted zone for `localtech.events`

## 5-Minute Setup

### Step 1: Install CDK (if not already installed)

```bash
npm install -g aws-cdk
```

### Step 2: Clone and Setup

```bash
cd localtech-auth
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Step 3: Configure Hosted Zone

```bash
# Find your hosted zone ID
aws route53 list-hosted-zones --query "HostedZones[?Name=='localtech.events.'].Id" --output text

# Set it as environment variable
export HOSTED_ZONE_ID=Z1234567890ABC  # Replace with your actual zone ID
```

### Step 4: Update OAuth Credentials (Temporary Placeholders)

For a quick test deployment, the placeholders will work but identity providers won't function.
To enable Google/Apple sign-in, see `CONFIGURATION.md` for detailed setup.

### Step 5: Deploy!

```bash
# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy the stack
cdk deploy

# Or use the helper script
./deploy.sh
```

### Step 6: Get Stack Outputs

After deployment completes, note these values:

```bash
aws cloudformation describe-stacks \
  --stack-name LocaltechAuthStack \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table
```

You'll see:
- **UserPoolId**: Use this in your application
- **UserPoolClientId**: Use this in your application
- **UserPoolDomain**: `https://account.localtech.events`
- **UserProfilesTableName**: DynamoDB table name
- **ProfileLambdaArn**: Lambda function ARN

## Test It Out

### Option 1: Using AWS Console

1. Go to Cognito in AWS Console
2. Find your user pool (`localtech-userpool`)
3. Use the App Integration tab to test the Hosted UI
4. Try creating a test user

### Option 2: Using AWS CLI

```bash
# Create a test user
aws cognito-idp admin-create-user \
  --user-pool-id YOUR_USER_POOL_ID \
  --username testuser@example.com \
  --user-attributes Name=email,Value=testuser@example.com \
  --temporary-password TempPass123!

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id YOUR_USER_POOL_ID \
  --username testuser@example.com \
  --password MyPassword123! \
  --permanent
```

### Option 3: Using the Hosted UI

Navigate to:
```
https://account.localtech.events/login?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=https://account.localtech.events/callback
```

## Next Steps

1. **Enable Social Sign-In**: Follow `CONFIGURATION.md` to set up Google and Apple OAuth
2. **Integrate with Your App**: Use the User Pool ID and Client ID in your application
3. **Customize**: Modify the stack in `localtech_auth/auth_stack.py` as needed
4. **Monitor**: Set up CloudWatch alarms for errors and usage

## Common First-Time Issues

### Issue: "Cannot retrieve value from context provider hosted-zone"

**Solution**: Set the `HOSTED_ZONE_ID` environment variable:
```bash
export HOSTED_ZONE_ID=Z1234567890ABC
```

### Issue: "CDKToolkit stack not found"

**Solution**: Bootstrap CDK first:
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

### Issue: Certificate validation pending

**Solution**: Wait 5-10 minutes for DNS validation to complete. ACM needs to verify domain ownership.

### Issue: OAuth providers don't work

**Solution**: Update the placeholder values with real OAuth credentials. See `CONFIGURATION.md`.

## Getting Help

- **Full Documentation**: See `README.md`
- **OAuth Setup**: See `CONFIGURATION.md`
- **Deployment Details**: See `DEPLOYMENT_SUMMARY.md`
- **AWS Cognito Docs**: https://docs.aws.amazon.com/cognito/

## Clean Up

To remove all resources and avoid charges:

```bash
cdk destroy
```

**Warning**: This will delete all user data. Back up first if needed!

---

**That's it!** You now have a production-ready authentication system running on AWS. 🎉
