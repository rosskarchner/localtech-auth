"""
Post-Confirmation Lambda Trigger

This Lambda function is triggered by Cognito after a user confirms their account.
It creates an initial user profile in DynamoDB with data from the Cognito event.
"""

import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any

dynamodb = boto3.resource('dynamodb')

TABLE_NAME = os.environ['TABLE_NAME']
table = dynamodb.Table(TABLE_NAME)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Cognito post-confirmation trigger handler.
    
    Creates a user profile in DynamoDB when a user confirms their account
    through email verification or social sign-in.
    """
    
    try:
        print(f"Post-confirmation event: {json.dumps(event)}")
        
        # Extract user attributes from the Cognito event
        user_attributes = event['request']['userAttributes']
        user_id = event['userName']
        
        # Create the user profile
        item = {
            'userId': user_id,
            'email': user_attributes.get('email', ''),
            'givenName': user_attributes.get('given_name', ''),
            'familyName': user_attributes.get('family_name', ''),
            'profilePicture': user_attributes.get('picture', ''),
            'emailVerified': user_attributes.get('email_verified', 'false') == 'true',
            'identityProvider': user_attributes.get('identities', '[]'),
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat(),
            'metadata': {
                'source': event.get('triggerSource', 'unknown'),
                'userPoolId': event['userPoolId'],
            }
        }
        
        # Store in DynamoDB
        table.put_item(Item=item)
        
        print(f"Created profile for user: {user_id}")
        
    except Exception as e:
        print(f"Error creating profile: {str(e)}")
        # Don't fail the confirmation process if profile creation fails
        # Log the error and continue
    
    # Always return the event to allow Cognito to continue
    return event
