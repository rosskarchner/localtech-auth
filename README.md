# localtech-auth

AWS CDK stack for Localtech authentication and user profile management.

## Overview

This CDK application creates a complete authentication system using AWS Cognito with social sign-in capabilities (Google and Apple ID) and a serverless user profile management system.

## Features

- **AWS Cognito User Pool** with custom domain (account.localtech.events)
- **Social Sign-In** with Google and Apple ID
- **Custom Domain** with SSL certificate
- **Serverless User Profiles** using DynamoDB and Lambda
- **Automated Profile Creation** via Cognito triggers
- **Email Verification** and secure password policies

## Architecture

### Components

1. **Cognito User Pool**: Manages user authentication and authorization
2. **Identity Providers**: Google and Apple for social sign-in
3. **Custom Domain**: account.localtech.events with Route53 and ACM
4. **DynamoDB Table**: Stores user profile data
5. **Lambda Functions**:
   - `ProfileLambda`: CRUD operations for user profiles
   - `PostConfirmationLambda`: Automatically creates profiles after sign-up

## Prerequisites

- AWS CLI configured with appropriate credentials
- Node.js and npm installed (for CDK)
- Python 3.14 or compatible version
- AWS account with Route53 hosted zone for localtech.events

## Setup

### 1. Install Dependencies

```bash
# Install CDK globally
npm install -g aws-cdk

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate.bat

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Identity Providers

Before deploying, you need to configure the OAuth credentials for Google and Apple:

#### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `https://account.localtech.events/oauth2/idpresponse`
6. Update the placeholder values in `localtech_auth/auth_stack.py`:
   - `GOOGLE_CLIENT_ID_PLACEHOLDER`
   - `GOOGLE_CLIENT_SECRET_PLACEHOLDER`

#### Apple Sign In Setup

1. Go to [Apple Developer Portal](https://developer.apple.com/)
2. Create a Service ID
3. Configure Sign in with Apple
4. Download the private key
5. Update the placeholder values in `localtech_auth/auth_stack.py`:
   - `APPLE_CLIENT_ID_PLACEHOLDER`
   - `APPLE_TEAM_ID_PLACEHOLDER`
   - `APPLE_KEY_ID_PLACEHOLDER`
   - `APPLE_PRIVATE_KEY_PLACEHOLDER`

**Security Best Practice**: Instead of hardcoding credentials, use AWS Secrets Manager or SSM Parameter Store to store sensitive values.

### 3. Deploy

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy the stack
cdk deploy
```

## Usage

### User Authentication Flow

1. Users navigate to `https://account.localtech.events`
2. Choose sign-in method:
   - Email/Password (traditional sign-up)
   - Google account
   - Apple ID
3. After confirmation, a user profile is automatically created in DynamoDB

### Profile Management

The Profile Lambda function can be invoked to manage user profiles:

```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Get user profile
response = lambda_client.invoke(
    FunctionName='ProfileLambda',
    Payload=json.dumps({
        'httpMethod': 'GET',
        'pathParameters': {'userId': 'user-123'}
    })
)

# Update profile
response = lambda_client.invoke(
    FunctionName='ProfileLambda',
    Payload=json.dumps({
        'httpMethod': 'POST',
        'body': {
            'userId': 'user-123',
            'givenName': 'John',
            'familyName': 'Doe',
            'metadata': {'preference': 'value'}
        }
    })
)
```

## Stack Outputs

After deployment, the stack provides these outputs:

- `UserPoolId`: Cognito User Pool ID
- `UserPoolClientId`: Client ID for web applications
- `UserPoolDomain`: Custom domain URL (account.localtech.events)
- `UserProfilesTableName`: DynamoDB table name
- `ProfileLambdaArn`: Lambda function ARN for profile management

## Development

### Project Structure

```
.
├── app.py                      # CDK app entry point
├── localtech_auth/
│   ├── __init__.py
│   └── auth_stack.py          # Main stack definition
├── lambda/
│   ├── profile/
│   │   └── index.py           # Profile management Lambda
│   └── post_confirmation/
│       └── index.py           # Post-confirmation trigger
├── tests/                      # Unit tests
├── requirements.txt            # Python dependencies
└── cdk.json                   # CDK configuration
```

### Testing

```bash
pytest tests/
```

### Useful CDK Commands

- `cdk ls` - List all stacks
- `cdk synth` - Synthesize CloudFormation template
- `cdk deploy` - Deploy stack
- `cdk diff` - Compare deployed stack with current state
- `cdk destroy` - Remove all resources

## Security Considerations

1. **Credentials**: Store OAuth credentials in AWS Secrets Manager
2. **Password Policy**: Enforces strong passwords (8+ chars, mixed case, numbers, symbols)
3. **Email Verification**: Required for all sign-ups
4. **HTTPS Only**: All endpoints use SSL/TLS
5. **DynamoDB Encryption**: Enabled by default
6. **IAM Least Privilege**: Lambda functions have minimal required permissions

## Cost Considerations

- Cognito: Free tier includes 50,000 MAUs
- DynamoDB: Pay-per-request pricing
- Lambda: Free tier includes 1M requests/month
- Route53: $0.50/month per hosted zone
- ACM: Free for public certificates

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]