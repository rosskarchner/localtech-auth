# Configuration Guide

This guide provides detailed instructions for configuring OAuth credentials for Google and Apple Sign-In.

## Prerequisites

- AWS Account with appropriate permissions
- Route53 hosted zone for `localtech.events`
- Google Cloud Platform account (for Google Sign-In)
- Apple Developer account (for Apple Sign-In)

## Google OAuth Configuration

### Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client ID"
5. Configure consent screen if prompted:
   - Application name: "Localtech Events"
   - User support email: Your email
   - Authorized domains: `localtech.events`

### Step 2: Configure OAuth Client

1. Application type: Web application
2. Name: "Localtech Auth"
3. Authorized JavaScript origins:
   - `https://account.localtech.events`
   - `http://localhost:3000` (for development)
4. Authorized redirect URIs:
   - `https://account.localtech.events/oauth2/idpresponse`
   - `http://localhost:3000/callback` (for development)

### Step 3: Save Credentials

After creating the OAuth client, you'll receive:
- Client ID (looks like: `1234567890-abc123xyz.apps.googleusercontent.com`)
- Client Secret (looks like: `GOCSPX-abc123xyz`)

**Important**: Keep these credentials secure!

## Apple Sign In Configuration

### Step 1: Create a Service ID

1. Go to [Apple Developer Portal](https://developer.apple.com/account/)
2. Navigate to "Certificates, Identifiers & Profiles"
3. Click "Identifiers" > "+" to create a new identifier
4. Select "Services IDs" and continue
5. Configure:
   - Description: "Localtech Auth"
   - Identifier: `com.localtech.auth` (or your preferred reverse domain)

### Step 2: Configure Sign in with Apple

1. Check "Sign in with Apple"
2. Click "Configure"
3. Add domains and subdomains:
   - Primary Domain: `localtech.events`
   - Subdomain: `account.localtech.events`
4. Add return URLs:
   - `https://account.localtech.events/oauth2/idpresponse`

### Step 3: Create a Key

1. In the left sidebar, click "Keys" > "+"
2. Configure:
   - Key Name: "Localtech Auth Key"
   - Enable "Sign in with Apple"
   - Configure with your Service ID
3. Download the private key file (`.p8` file)
   - **Important**: This file can only be downloaded once!
   - Store it securely

### Step 4: Collect Required Information

You'll need:
- **Client ID**: Your Service ID (e.g., `com.localtech.auth`)
- **Team ID**: Found in the top-right of Apple Developer portal (e.g., `A1B2C3D4E5`)
- **Key ID**: Found when viewing your key (e.g., `F6G7H8I9J0`)
- **Private Key**: Contents of the `.p8` file you downloaded

## Storing Credentials

You have three options for storing OAuth credentials:

### Option 1: AWS Secrets Manager (Recommended)

Use the provided helper script:

```bash
python3 setup_credentials.py
```

This will interactively prompt for credentials and store them securely in AWS Secrets Manager.

Then update `localtech_auth/auth_stack.py` to read from Secrets Manager:

```python
# Example code to read from Secrets Manager
google_secret = secretsmanager.Secret.from_secret_name_v2(
    self, "GoogleSecret",
    secret_name="localtech-auth/google-oauth"
)

google_provider = cognito.UserPoolIdentityProviderGoogle(
    self, "GoogleProvider",
    user_pool=user_pool,
    client_id=google_secret.secret_value_from_json("client_id").to_string(),
    client_secret=google_secret.secret_value_from_json("client_secret").to_string(),
    # ...
)
```

### Option 2: AWS Systems Manager Parameter Store

Store credentials as SecureString parameters:

```bash
aws ssm put-parameter \
  --name /localtech-auth/google/client-id \
  --value "YOUR_GOOGLE_CLIENT_ID" \
  --type SecureString

aws ssm put-parameter \
  --name /localtech-auth/google/client-secret \
  --value "YOUR_GOOGLE_CLIENT_SECRET" \
  --type SecureString
```

### Option 3: Direct in Code (Not Recommended for Production)

For development/testing only, update the placeholder values in `localtech_auth/auth_stack.py`:

```python
google_provider = cognito.UserPoolIdentityProviderGoogle(
    self, "GoogleProvider",
    user_pool=user_pool,
    client_id="YOUR_ACTUAL_GOOGLE_CLIENT_ID",
    client_secret="YOUR_ACTUAL_GOOGLE_CLIENT_SECRET",
    # ...
)

apple_provider = cognito.UserPoolIdentityProviderApple(
    self, "AppleProvider",
    user_pool=user_pool,
    client_id="YOUR_ACTUAL_APPLE_CLIENT_ID",
    team_id="YOUR_ACTUAL_APPLE_TEAM_ID",
    key_id="YOUR_ACTUAL_APPLE_KEY_ID",
    private_key="YOUR_ACTUAL_APPLE_PRIVATE_KEY",
    # ...
)
```

**Warning**: Never commit actual credentials to version control!

## Updating Credentials After Deployment

If you need to update OAuth credentials after the stack is deployed:

### Using AWS Console

1. Go to Amazon Cognito console
2. Select your User Pool (`localtech-userpool`)
3. Navigate to "Sign-in experience" > "Federated identity provider sign-in"
4. Click on the provider (Google or Apple)
5. Update the credentials
6. Save changes

### Using AWS CLI

```bash
# Update Google provider
aws cognito-idp update-identity-provider \
  --user-pool-id YOUR_USER_POOL_ID \
  --provider-name Google \
  --provider-details client_id="NEW_CLIENT_ID",client_secret="NEW_CLIENT_SECRET"

# Update Apple provider
aws cognito-idp update-identity-provider \
  --user-pool-id YOUR_USER_POOL_ID \
  --provider-name SignInWithApple \
  --provider-details client_id="NEW_CLIENT_ID",team_id="TEAM_ID",key_id="KEY_ID",private_key="PRIVATE_KEY"
```

## Testing OAuth Integration

### Testing Google Sign-In

1. Navigate to `https://account.localtech.events`
2. Click "Sign in with Google"
3. Select your Google account
4. Authorize the application
5. You should be redirected back with authentication complete

### Testing Apple Sign-In

1. Navigate to `https://account.localtech.events`
2. Click "Sign in with Apple"
3. Sign in with your Apple ID
4. Authorize the application
5. You should be redirected back with authentication complete

## Troubleshooting

### Google OAuth Errors

**Error: `redirect_uri_mismatch`**
- Verify the redirect URI in Google Cloud Console matches exactly
- Must be: `https://account.localtech.events/oauth2/idpresponse`

**Error: `invalid_client`**
- Check that Client ID and Client Secret are correct
- Ensure the OAuth client is enabled

### Apple Sign In Errors

**Error: Invalid client**
- Verify Service ID matches the client_id in configuration
- Check that the domain is verified in Apple Developer Portal

**Error: Invalid redirect_uri**
- Verify return URL in Apple Developer Portal
- Must be: `https://account.localtech.events/oauth2/idpresponse`

**Error: Invalid key**
- Ensure the private key is formatted correctly
- Check that Key ID and Team ID are correct
- Verify the key is not expired

### General Troubleshooting

1. Check CloudWatch Logs for Lambda functions:
   - `/aws/lambda/LocaltechAuthStack-ProfileLambda*`
   - `/aws/lambda/LocaltechAuthStack-PostConfirmationLambda*`

2. Verify DNS propagation:
   ```bash
   dig account.localtech.events
   ```

3. Check certificate status:
   ```bash
   aws acm list-certificates --region us-east-1
   ```

4. Test Cognito endpoints:
   ```bash
   curl https://account.localtech.events/.well-known/jwks.json
   ```

## Security Best Practices

1. **Rotate credentials regularly**: Update OAuth credentials every 90 days
2. **Use least privilege**: Grant only necessary permissions to Lambda functions
3. **Enable MFA**: Require multi-factor authentication for sensitive operations
4. **Monitor access**: Set up CloudWatch alarms for unusual authentication patterns
5. **Keep secrets secure**: Never commit credentials to version control
6. **Use Secrets Manager**: Store credentials in AWS Secrets Manager with rotation enabled
7. **Enable audit logging**: Use CloudTrail to log all API calls

## Next Steps

After configuring OAuth:

1. Deploy or update the stack: `./deploy.sh`
2. Test authentication flows with both Google and Apple
3. Integrate the User Pool with your web application
4. Set up monitoring and alerts
5. Configure backup and disaster recovery

## Support

For issues specific to:
- **Google OAuth**: [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- **Apple Sign In**: [Apple Sign In Documentation](https://developer.apple.com/sign-in-with-apple/)
- **AWS Cognito**: [Amazon Cognito Documentation](https://docs.aws.amazon.com/cognito/)
