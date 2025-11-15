#!/usr/bin/env python3
"""
Helper script to set up OAuth credentials in AWS Secrets Manager.

This script helps you securely store Google and Apple OAuth credentials
instead of hardcoding them in the stack.
"""

import boto3
import json
import sys
from typing import Dict, Any

secrets_manager = boto3.client('secretsmanager')


def create_or_update_secret(secret_name: str, secret_value: Dict[str, Any]) -> None:
    """Create or update a secret in AWS Secrets Manager."""
    try:
        # Try to create the secret
        response = secrets_manager.create_secret(
            Name=secret_name,
            SecretString=json.dumps(secret_value),
            Description=f"OAuth credentials for {secret_name}"
        )
        print(f"✓ Created secret: {secret_name}")
        print(f"  ARN: {response['ARN']}")
    except secrets_manager.exceptions.ResourceExistsException:
        # Secret already exists, update it
        response = secrets_manager.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(secret_value)
        )
        print(f"✓ Updated secret: {secret_name}")
        print(f"  ARN: {response['ARN']}")


def setup_google_credentials():
    """Interactively set up Google OAuth credentials."""
    print("\n=== Google OAuth Setup ===")
    print("Get these values from: https://console.cloud.google.com/")
    
    client_id = input("Enter Google Client ID: ").strip()
    client_secret = input("Enter Google Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Both Client ID and Client Secret are required")
        return False
    
    secret_value = {
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    create_or_update_secret("localtech-auth/google-oauth", secret_value)
    return True


def setup_apple_credentials():
    """Interactively set up Apple Sign In credentials."""
    print("\n=== Apple Sign In Setup ===")
    print("Get these values from: https://developer.apple.com/")
    
    client_id = input("Enter Apple Service ID (Client ID): ").strip()
    team_id = input("Enter Apple Team ID: ").strip()
    key_id = input("Enter Apple Key ID: ").strip()
    
    print("\nEnter the Apple Private Key (paste the entire key including BEGIN/END lines):")
    print("Press Enter twice when done:")
    private_key_lines = []
    while True:
        line = input()
        if line == "" and private_key_lines and private_key_lines[-1] == "":
            break
        private_key_lines.append(line)
    
    private_key = "\n".join(private_key_lines[:-1])  # Remove the last empty line
    
    if not all([client_id, team_id, key_id, private_key]):
        print("❌ All fields are required")
        return False
    
    secret_value = {
        "client_id": client_id,
        "team_id": team_id,
        "key_id": key_id,
        "private_key": private_key
    }
    
    create_or_update_secret("localtech-auth/apple-signin", secret_value)
    return True


def retrieve_credentials():
    """Display stored credentials (redacted)."""
    print("\n=== Stored Credentials ===")
    
    secrets = [
        "localtech-auth/google-oauth",
        "localtech-auth/apple-signin"
    ]
    
    for secret_name in secrets:
        try:
            response = secrets_manager.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(response['SecretString'])
            print(f"\n{secret_name}:")
            for key in secret_data.keys():
                print(f"  {key}: [REDACTED]")
        except secrets_manager.exceptions.ResourceNotFoundException:
            print(f"\n{secret_name}: Not configured")
        except Exception as e:
            print(f"\n{secret_name}: Error - {str(e)}")


def main():
    """Main function."""
    print("Localtech Auth - OAuth Credentials Setup")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        retrieve_credentials()
        return
    
    print("\nThis script will help you securely store OAuth credentials")
    print("in AWS Secrets Manager instead of hardcoding them.\n")
    
    while True:
        print("\nOptions:")
        print("1. Set up Google OAuth credentials")
        print("2. Set up Apple Sign In credentials")
        print("3. View stored credentials (redacted)")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            setup_google_credentials()
        elif choice == "2":
            setup_apple_credentials()
        elif choice == "3":
            retrieve_credentials()
        elif choice == "4":
            print("\nGoodbye!")
            break
        else:
            print("❌ Invalid choice")
    
    print("\nNext steps:")
    print("1. Update localtech_auth/auth_stack.py to read from Secrets Manager")
    print("2. Deploy the stack with: cdk deploy")


if __name__ == "__main__":
    main()
