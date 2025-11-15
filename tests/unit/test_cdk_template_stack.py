import aws_cdk as core
import aws_cdk.assertions as assertions

from localtech_auth.auth_stack import LocaltechAuthStack


def test_cognito_user_pool_created():
    """Test that Cognito User Pool is created with correct properties."""
    app = core.App()
    stack = LocaltechAuthStack(app, "TestStack", hosted_zone_id="Z1234567890ABC")
    template = assertions.Template.from_stack(stack)

    # Check that User Pool is created
    template.has_resource_properties("AWS::Cognito::UserPool", {
        "UserPoolName": "localtech-userpool",
        "AutoVerifiedAttributes": ["email"],
    })


def test_cognito_user_pool_domain_created():
    """Test that Cognito User Pool Domain is created."""
    app = core.App()
    stack = LocaltechAuthStack(app, "TestStack", hosted_zone_id="Z1234567890ABC")
    template = assertions.Template.from_stack(stack)

    # Check that custom domain is created
    template.has_resource_properties("AWS::Cognito::UserPoolDomain", {
        "Domain": "account.localtech.events",
    })


def test_dynamodb_table_created():
    """Test that DynamoDB table for user profiles is created."""
    app = core.App()
    stack = LocaltechAuthStack(app, "TestStack", hosted_zone_id="Z1234567890ABC")
    template = assertions.Template.from_stack(stack)

    # Check that table is created with correct properties
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "TableName": "localtech-user-profiles",
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [
            {"AttributeName": "userId", "KeyType": "HASH"}
        ],
    })


def test_lambda_functions_created():
    """Test that Lambda functions are created."""
    app = core.App()
    stack = LocaltechAuthStack(app, "TestStack", hosted_zone_id="Z1234567890ABC")
    template = assertions.Template.from_stack(stack)

    # Check that our Lambda functions are created (CDK may create additional custom resource lambdas)
    # So we check for at least 2 functions
    functions = template.find_resources("AWS::Lambda::Function")
    assert len(functions) >= 2, f"Expected at least 2 Lambda functions, found {len(functions)}"
    
    # Check runtime is Python 3.13 for our functions
    template.has_resource_properties("AWS::Lambda::Function", {
        "Runtime": "python3.13",
    })


def test_certificate_created():
    """Test that ACM certificate is created for the domain."""
    app = core.App()
    stack = LocaltechAuthStack(app, "TestStack", hosted_zone_id="Z1234567890ABC")
    template = assertions.Template.from_stack(stack)

    # Check that certificate is created
    template.has_resource_properties("AWS::CertificateManager::Certificate", {
        "DomainName": "account.localtech.events",
        "ValidationMethod": "DNS",
    })


def test_identity_providers_configured():
    """Test that Google and Apple identity providers are configured."""
    app = core.App()
    stack = LocaltechAuthStack(app, "TestStack", hosted_zone_id="Z1234567890ABC")
    template = assertions.Template.from_stack(stack)

    # Check that identity providers exist
    template.resource_count_is("AWS::Cognito::UserPoolIdentityProvider", 2)


def test_iam_roles_created():
    """Test that IAM roles are created for Lambda functions."""
    app = core.App()
    stack = LocaltechAuthStack(app, "TestStack", hosted_zone_id="Z1234567890ABC")
    template = assertions.Template.from_stack(stack)

    # Check that IAM roles are created (CDK may create additional roles for custom resources)
    roles = template.find_resources("AWS::IAM::Role")
    assert len(roles) >= 2, f"Expected at least 2 IAM roles, found {len(roles)}"
