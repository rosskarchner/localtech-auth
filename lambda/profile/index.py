"""
User Profile Management Lambda Function

This Lambda function handles CRUD operations for user profiles stored in DynamoDB.
It can be invoked directly or through API Gateway.
"""

import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any

dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')

TABLE_NAME = os.environ['TABLE_NAME']
USER_POOL_ID = os.environ['USER_POOL_ID']

table = dynamodb.Table(TABLE_NAME)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for user profile operations.
    
    Supported operations:
    - GET: Retrieve user profile
    - POST: Create/Update user profile
    - DELETE: Delete user profile
    """
    
    try:
        http_method = event.get('httpMethod', 'POST')
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
        
        user_id = event.get('pathParameters', {}).get('userId') or body.get('userId')
        
        if http_method == 'GET':
            return get_profile(user_id)
        elif http_method == 'POST' or http_method == 'PUT':
            return create_or_update_profile(user_id, body)
        elif http_method == 'DELETE':
            return delete_profile(user_id)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unsupported method'})
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def get_profile(user_id: str) -> Dict[str, Any]:
    """Retrieve a user profile from DynamoDB."""
    if not user_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'userId is required'})
        }
    
    response = table.get_item(Key={'userId': user_id})
    
    if 'Item' not in response:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Profile not found'})
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps(response['Item'], default=str)
    }


def create_or_update_profile(user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a user profile in DynamoDB."""
    if not user_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'userId is required'})
        }
    
    # Prepare item
    item = {
        'userId': user_id,
        'email': profile_data.get('email', ''),
        'givenName': profile_data.get('givenName', ''),
        'familyName': profile_data.get('familyName', ''),
        'profilePicture': profile_data.get('profilePicture', ''),
        'metadata': profile_data.get('metadata', {}),
        'updatedAt': datetime.utcnow().isoformat(),
    }
    
    # Add createdAt only for new profiles
    try:
        existing = table.get_item(Key={'userId': user_id})
        if 'Item' in existing:
            item['createdAt'] = existing['Item'].get('createdAt', datetime.utcnow().isoformat())
        else:
            item['createdAt'] = datetime.utcnow().isoformat()
    except Exception:
        item['createdAt'] = datetime.utcnow().isoformat()
    
    table.put_item(Item=item)
    
    return {
        'statusCode': 200,
        'body': json.dumps(item, default=str)
    }


def delete_profile(user_id: str) -> Dict[str, Any]:
    """Delete a user profile from DynamoDB."""
    if not user_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'userId is required'})
        }
    
    table.delete_item(Key={'userId': user_id})
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Profile deleted successfully'})
    }
