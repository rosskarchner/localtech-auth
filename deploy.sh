#!/bin/bash
set -e

# Deployment script for Localtech Auth CDK Stack

echo "=== Localtech Auth Deployment Script ==="
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS CLI is not configured or credentials are invalid"
    echo "Please run: aws configure"
    exit 1
fi

# Get AWS account and region
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo "✓ AWS Account: $AWS_ACCOUNT"
echo "✓ AWS Region: $AWS_REGION"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Check for hosted zone
if [ -z "$HOSTED_ZONE_ID" ]; then
    echo "Looking up Route53 hosted zone for localtech.events..."
    HOSTED_ZONE_ID=$(aws route53 list-hosted-zones --query "HostedZones[?Name=='localtech.events.'].Id" --output text | cut -d'/' -f3)
    
    if [ -z "$HOSTED_ZONE_ID" ]; then
        echo "⚠️  Warning: Could not find hosted zone for localtech.events"
        echo "Please set HOSTED_ZONE_ID environment variable or create the hosted zone first"
        echo ""
        echo "You can create it with:"
        echo "  aws route53 create-hosted-zone --name localtech.events --caller-reference \$(date +%s)"
        echo ""
        read -p "Do you want to continue without a hosted zone? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "✓ Found hosted zone: $HOSTED_ZONE_ID"
        export HOSTED_ZONE_ID
    fi
fi

# Check for OAuth credentials
echo ""
echo "Checking OAuth credentials..."
if grep -q "GOOGLE_CLIENT_ID_PLACEHOLDER" localtech_auth/auth_stack.py || \
   grep -q "APPLE_CLIENT_ID_PLACEHOLDER" localtech_auth/auth_stack.py; then
    echo "⚠️  OAuth credentials are still using placeholder values"
    echo ""
    echo "You need to update the OAuth credentials in localtech_auth/auth_stack.py"
    echo "or use AWS Secrets Manager to store them securely."
    echo ""
    echo "Would you like to:"
    echo "  1. Continue anyway (you can update credentials later)"
    echo "  2. Exit and configure credentials first"
    echo ""
    read -p "Enter choice (1 or 2): " choice
    if [ "$choice" != "1" ]; then
        echo ""
        echo "Please update OAuth credentials and run this script again"
        echo "You can use: python3 setup_credentials.py"
        exit 1
    fi
fi

# Bootstrap CDK if needed (only needs to be done once per account/region)
echo ""
echo "Checking CDK bootstrap status..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $AWS_REGION &> /dev/null; then
    echo "CDK is not bootstrapped in this account/region"
    read -p "Would you like to bootstrap CDK now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION
    else
        echo "⚠️  Skipping bootstrap. Stack deployment may fail if not already bootstrapped."
    fi
else
    echo "✓ CDK is already bootstrapped"
fi

# Synthesize the stack
echo ""
echo "Synthesizing CloudFormation template..."
cdk synth

# Deploy the stack
echo ""
echo "Deploying stack..."
echo "You will be prompted to approve security-sensitive changes (IAM roles, etc.)"
echo ""

cdk deploy --require-approval broadening

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Stack outputs have been saved. You can view them with:"
echo "  aws cloudformation describe-stacks --stack-name LocaltechAuthStack --query 'Stacks[0].Outputs'"
echo ""
echo "Next steps:"
echo "1. Update OAuth credentials in Cognito console or via AWS Secrets Manager"
echo "2. Configure your web application with the User Pool ID and Client ID"
echo "3. Test authentication at https://account.localtech.events"
