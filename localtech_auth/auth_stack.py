from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    CfnOutput,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_certificatemanager as acm,
    aws_iam as iam,
)
from constructs import Construct

class LocaltechAuthStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, hosted_zone_id: str = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Look up or import the hosted zone for localtech.events
        if hosted_zone_id:
            hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
                self, "LocaltechHostedZone",
                hosted_zone_id=hosted_zone_id,
                zone_name="localtech.events"
            )
        else:
            # If no zone ID provided, look it up (requires account/region)
            hosted_zone = route53.HostedZone.from_lookup(
                self, "LocaltechHostedZone",
                domain_name="localtech.events"
            )

        # Create certificate for account.localtech.events
        certificate = acm.Certificate(
            self, "AccountCertificate",
            domain_name="account.localtech.events",
            validation=acm.CertificateValidation.from_dns(hosted_zone)
        )

        # Create Cognito User Pool
        user_pool = cognito.UserPool(
            self, "LocaltechUserPool",
            user_pool_name="localtech-userpool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(
                email=True,
            ),
            auto_verify=cognito.AutoVerifiedAttrs(
                email=True,
            ),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=True,
                ),
                given_name=cognito.StandardAttribute(
                    required=False,
                    mutable=True,
                ),
                family_name=cognito.StandardAttribute(
                    required=False,
                    mutable=True,
                ),
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Add custom domain for Cognito
        user_pool_domain = user_pool.add_domain(
            "CognitoDomain",
            custom_domain=cognito.CustomDomainOptions(
                domain_name="account.localtech.events",
                certificate=certificate,
            )
        )

        # Create A record for the custom domain
        route53.ARecord(
            self, "AccountAliasRecord",
            zone=hosted_zone,
            record_name="account",
            target=route53.RecordTarget.from_alias(
                targets.UserPoolDomainTarget(user_pool_domain)
            )
        )

        # Create User Pool Client for web application
        user_pool_client = user_pool.add_client(
            "WebAppClient",
            user_pool_client_name="localtech-web-client",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=True,
                ),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE,
                ],
                callback_urls=[
                    "https://account.localtech.events/callback",
                    "http://localhost:3000/callback",
                ],
                logout_urls=[
                    "https://account.localtech.events/logout",
                    "http://localhost:3000/logout",
                ],
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.GOOGLE,
                cognito.UserPoolClientIdentityProvider.APPLE,
            ],
        )

        # Configure Google Identity Provider
        # Note: You'll need to configure these values in AWS Secrets Manager or SSM Parameter Store
        google_provider = cognito.UserPoolIdentityProviderGoogle(
            self, "GoogleProvider",
            user_pool=user_pool,
            client_id="GOOGLE_CLIENT_ID_PLACEHOLDER",
            client_secret="GOOGLE_CLIENT_SECRET_PLACEHOLDER",
            scopes=["profile", "email", "openid"],
            attribute_mapping=cognito.AttributeMapping(
                email=cognito.ProviderAttribute.GOOGLE_EMAIL,
                given_name=cognito.ProviderAttribute.GOOGLE_GIVEN_NAME,
                family_name=cognito.ProviderAttribute.GOOGLE_FAMILY_NAME,
                profile_picture=cognito.ProviderAttribute.GOOGLE_PICTURE,
            )
        )

        # Configure Apple Identity Provider
        # Note: You'll need to configure these values in AWS Secrets Manager or SSM Parameter Store
        apple_provider = cognito.UserPoolIdentityProviderApple(
            self, "AppleProvider",
            user_pool=user_pool,
            client_id="APPLE_CLIENT_ID_PLACEHOLDER",
            team_id="APPLE_TEAM_ID_PLACEHOLDER",
            key_id="APPLE_KEY_ID_PLACEHOLDER",
            private_key="APPLE_PRIVATE_KEY_PLACEHOLDER",
            scopes=["email", "name"],
            attribute_mapping=cognito.AttributeMapping(
                email=cognito.ProviderAttribute.APPLE_EMAIL,
                given_name=cognito.ProviderAttribute.APPLE_FIRST_NAME,
                family_name=cognito.ProviderAttribute.APPLE_LAST_NAME,
            )
        )

        # Ensure client depends on identity providers
        user_pool_client.node.add_dependency(google_provider)
        user_pool_client.node.add_dependency(apple_provider)

        # Create DynamoDB table for user profiles
        user_profiles_table = dynamodb.Table(
            self, "UserProfilesTable",
            table_name="localtech-user-profiles",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )

        # Add GSI for email lookup
        user_profiles_table.add_global_secondary_index(
            index_name="EmailIndex",
            partition_key=dynamodb.Attribute(
                name="email",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Create Lambda function for user profile management
        profile_lambda = lambda_.Function(
            self, "ProfileLambda",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            code=lambda_.Code.from_asset("lambda/profile"),
            environment={
                "TABLE_NAME": user_profiles_table.table_name,
                "USER_POOL_ID": user_pool.user_pool_id,
            },
            timeout=Duration.seconds(30),
        )

        # Grant Lambda permissions to access DynamoDB and Cognito
        user_profiles_table.grant_read_write_data(profile_lambda)
        
        profile_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "cognito-idp:AdminGetUser",
                    "cognito-idp:ListUsers",
                ],
                resources=[user_pool.user_pool_arn],
            )
        )

        # Create Lambda for Cognito triggers (post-confirmation)
        post_confirmation_lambda = lambda_.Function(
            self, "PostConfirmationLambda",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            code=lambda_.Code.from_asset("lambda/post_confirmation"),
            environment={
                "TABLE_NAME": user_profiles_table.table_name,
            },
            timeout=Duration.seconds(30),
        )

        # Grant Lambda permissions to write to DynamoDB
        user_profiles_table.grant_write_data(post_confirmation_lambda)

        # Add Lambda trigger to User Pool
        user_pool.add_trigger(
            cognito.UserPoolOperation.POST_CONFIRMATION,
            post_confirmation_lambda
        )

        # Outputs
        CfnOutput(
            self, "UserPoolId",
            value=user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )

        CfnOutput(
            self, "UserPoolClientId",
            value=user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID"
        )

        CfnOutput(
            self, "UserPoolDomain",
            value=f"https://account.localtech.events",
            description="Cognito Custom Domain"
        )

        CfnOutput(
            self, "UserProfilesTableName",
            value=user_profiles_table.table_name,
            description="DynamoDB User Profiles Table Name"
        )

        CfnOutput(
            self, "ProfileLambdaArn",
            value=profile_lambda.function_arn,
            description="Profile Management Lambda ARN"
        )
