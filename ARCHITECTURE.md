# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         End Users                                    │
│                    (Web/Mobile Applications)                         │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Route53 DNS + CloudFront                           │
│                  account.localtech.events                            │
│                    (SSL/TLS via ACM)                                 │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AWS Cognito User Pool                             │
│                   (localtech-userpool)                               │
│                                                                       │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Email/Password │  │ Google OAuth │  │ Apple Sign In│            │
│  │   Sign-In      │  │   Provider   │  │   Provider   │            │
│  └────────────────┘  └──────────────┘  └──────────────┘            │
│                                                                       │
│  Features:                                                           │
│  • Email verification                                                │
│  • Strong password policy                                           │
│  • Account recovery                                                  │
│  • OAuth 2.0 / OpenID Connect                                       │
│  • JWT token issuance                                               │
└────────┬────────────────────────────────────────┬───────────────────┘
         │                                        │
         │ Post-Confirmation Trigger              │ Authentication Events
         │                                        │
         ▼                                        ▼
┌──────────────────────────┐          ┌─────────────────────────┐
│  PostConfirmationLambda  │          │   User Application      │
│     (Python 3.13)        │          │  (Your Web/Mobile App)  │
│                          │          │                         │
│  • Creates user profile  │          │  • Receives JWT tokens  │
│  • Extracts user data    │          │  • Validates tokens     │
│  • Stores in DynamoDB    │          │  • Manages sessions     │
└────────┬─────────────────┘          └─────────┬───────────────┘
         │                                      │
         │                                      │ Profile API Calls
         │                                      │
         ▼                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DynamoDB Table                            │
│                   (localtech-user-profiles)                      │
│                                                                   │
│  Schema:                                                         │
│  • userId (Partition Key)                                       │
│  • email                                                        │
│  • givenName                                                    │
│  • familyName                                                   │
│  • profilePicture                                               │
│  • metadata                                                     │
│  • createdAt / updatedAt                                        │
│                                                                   │
│  Global Secondary Index:                                         │
│  • EmailIndex (email as partition key)                          │
│                                                                   │
│  Features:                                                       │
│  • Pay-per-request billing                                      │
│  • Point-in-time recovery                                       │
│  • Stream enabled                                               │
└──────────────────────┬──────────────────────────────────────────┘
                       ▲
                       │
                       │ Read/Write Operations
                       │
┌──────────────────────┴──────────────────────────┐
│              ProfileLambda                       │
│             (Python 3.13)                        │
│                                                  │
│  Operations:                                    │
│  • GET /profile/{userId}                        │
│  • POST /profile (create/update)                │
│  • DELETE /profile/{userId}                     │
│                                                  │
│  Integrations:                                  │
│  • DynamoDB read/write                          │
│  • Cognito user lookup                          │
└─────────────────────────────────────────────────┘
```

## Authentication Flow

### 1. Email/Password Sign-Up

```
User → Cognito Sign-Up
  ↓
Email Verification Sent
  ↓
User Confirms Email
  ↓
PostConfirmationLambda Triggered
  ↓
User Profile Created in DynamoDB
  ↓
User Authenticated
  ↓
JWT Tokens Issued
```

### 2. Google Sign-In Flow

```
User Clicks "Sign in with Google"
  ↓
Redirect to Google OAuth
  ↓
User Authenticates with Google
  ↓
Google Redirects to Cognito
  ↓
Cognito Creates/Links User
  ↓
PostConfirmationLambda (if new user)
  ↓
User Profile Created/Updated
  ↓
JWT Tokens Issued
```

### 3. Apple Sign-In Flow

```
User Clicks "Sign in with Apple"
  ↓
Redirect to Apple Sign In
  ↓
User Authenticates with Apple ID
  ↓
Apple Redirects to Cognito
  ↓
Cognito Creates/Links User
  ↓
PostConfirmationLambda (if new user)
  ↓
User Profile Created/Updated
  ↓
JWT Tokens Issued
```

## Data Flow

### Profile Creation (Automatic)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Cognito    │────▶│PostConfirm   │────▶│  DynamoDB    │
│   Trigger    │     │   Lambda     │     │    Table     │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            │ Extract user attributes:
                            │ • userId
                            │ • email
                            │ • givenName
                            │ • familyName
                            │ • profilePicture
                            │ • identityProvider
                            ▼
                     Store in DynamoDB
```

### Profile Management (API)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Application  │────▶│  Profile     │────▶│  DynamoDB    │
│   (Client)   │◀────│   Lambda     │◀────│    Table     │
└──────────────┘     └──────────────┘     └──────────────┘
      │                     │
      │ Operations:         │ Methods:
      │ • Get profile       │ • get_profile()
      │ • Update profile    │ • create_or_update_profile()
      │ • Delete profile    │ • delete_profile()
      ▼                     ▼
   JWT Token         DynamoDB Operations
  Validation        (Read/Write/Delete)
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Network Layer                                            │
│     • HTTPS only (TLS 1.2+)                                 │
│     • ACM managed certificates                              │
│     • CloudFront distribution                               │
│                                                               │
│  2. Authentication Layer                                     │
│     • Cognito JWT tokens                                    │
│     • Email verification                                    │
│     • Strong password policy                                │
│     • OAuth 2.0 / OpenID Connect                           │
│                                                               │
│  3. Authorization Layer                                      │
│     • IAM roles with least privilege                        │
│     • Lambda execution roles                                │
│     • Resource-based policies                               │
│                                                               │
│  4. Data Layer                                              │
│     • DynamoDB encryption at rest                           │
│     • Point-in-time recovery                                │
│     • Stream encryption                                     │
│                                                               │
│  5. Application Layer                                        │
│     • Input validation                                      │
│     • Error handling                                        │
│     • CloudWatch logging                                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## IAM Permissions Model

```
┌──────────────────────────────────────────────────────────────┐
│                   ProfileLambda IAM Role                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  DynamoDB Permissions:                                       │
│  • dynamodb:GetItem                                          │
│  • dynamodb:PutItem                                          │
│  • dynamodb:UpdateItem                                       │
│  • dynamodb:DeleteItem                                       │
│  • dynamodb:Query                                            │
│  • dynamodb:Scan                                             │
│                                                               │
│  Cognito Permissions:                                        │
│  • cognito-idp:AdminGetUser                                  │
│  • cognito-idp:ListUsers                                     │
│                                                               │
│  CloudWatch Logs:                                            │
│  • logs:CreateLogGroup                                       │
│  • logs:CreateLogStream                                      │
│  • logs:PutLogEvents                                         │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│             PostConfirmationLambda IAM Role                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  DynamoDB Permissions:                                       │
│  • dynamodb:PutItem                                          │
│  • dynamodb:UpdateItem                                       │
│                                                               │
│  CloudWatch Logs:                                            │
│  • logs:CreateLogGroup                                       │
│  • logs:CreateLogStream                                      │
│  • logs:PutLogEvents                                         │
└──────────────────────────────────────────────────────────────┘
```

## Scalability & Performance

### Horizontal Scaling

- **Cognito**: Automatically scales to millions of users
- **Lambda**: Concurrent execution up to account limits
- **DynamoDB**: Auto-scaling with pay-per-request
- **CloudFront**: Global edge network

### Performance Characteristics

- **Authentication**: ~100-200ms (token generation)
- **Profile Read**: ~10-50ms (DynamoDB single-item read)
- **Profile Write**: ~20-100ms (DynamoDB write + indexes)
- **Lambda Cold Start**: ~1-3 seconds (Python 3.13)
- **Lambda Warm**: ~50-200ms

## Monitoring & Observability

```
┌────────────────────────────────────────────────────────────┐
│                   CloudWatch Metrics                        │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Cognito Metrics:                                          │
│  • SignInSuccesses / SignInFailures                        │
│  • TokenRefreshSuccesses                                   │
│  • UserAuthentication                                      │
│                                                             │
│  Lambda Metrics:                                           │
│  • Invocations                                             │
│  • Errors / Throttles                                      │
│  • Duration / Concurrent Executions                        │
│                                                             │
│  DynamoDB Metrics:                                         │
│  • ConsumedReadCapacity                                    │
│  • ConsumedWriteCapacity                                   │
│  • SystemErrors / UserErrors                               │
│                                                             │
│  CloudWatch Logs:                                          │
│  • /aws/lambda/ProfileLambda                               │
│  • /aws/lambda/PostConfirmationLambda                      │
└────────────────────────────────────────────────────────────┘
```

## Disaster Recovery

### Backup Strategy

1. **DynamoDB**
   - Point-in-time recovery enabled
   - Continuous backups (35 days)
   - Can restore to any second

2. **Cognito**
   - User pool configuration backed by CDK
   - Users can be exported via AWS CLI
   - Consider periodic user backups

3. **Infrastructure**
   - Infrastructure as Code (CDK)
   - All configuration in version control
   - Can recreate entire stack from code

### Recovery Procedures

**Scenario 1: DynamoDB Table Deletion**
```bash
# Restore from point-in-time backup
aws dynamodb restore-table-to-point-in-time \
  --source-table-name localtech-user-profiles \
  --target-table-name localtech-user-profiles-restored \
  --restore-date-time 2024-01-01T00:00:00Z
```

**Scenario 2: Stack Deletion**
```bash
# Redeploy from CDK
cdk deploy
```

**Scenario 3: Lambda Function Issues**
```bash
# Rollback to previous version
aws lambda update-function-code \
  --function-name ProfileLambda \
  --s3-bucket previous-version-bucket \
  --s3-key previous-version.zip
```

## Cost Optimization

### Cost Breakdown (Estimated Monthly)

```
Service                  Free Tier              Cost (1K users)
────────────────────────────────────────────────────────────────
Cognito                 50K MAUs free           $0
DynamoDB                25GB + 200M requests    $0-2
Lambda                  1M requests free        $0-1
Route53                 N/A                     $0.50
ACM                     Free                    $0
CloudWatch Logs         5GB ingestion           $0-1
────────────────────────────────────────────────────────────────
TOTAL                                           ~$1-5/month
```

### Optimization Tips

1. **Use DynamoDB on-demand pricing** for unpredictable traffic
2. **Set CloudWatch log retention** to 7-30 days
3. **Use Lambda reserved concurrency** for cost predictability
4. **Enable DynamoDB TTL** for temporary data
5. **Monitor and set alarms** for unusual usage

---

## Summary

This architecture provides:

✅ **Scalability**: Handles growth from 0 to millions of users
✅ **Security**: Multiple layers of protection
✅ **Reliability**: 99.9%+ uptime with AWS services
✅ **Performance**: Sub-second response times
✅ **Cost-Effective**: Pay only for what you use
✅ **Maintainable**: Infrastructure as Code with CDK
