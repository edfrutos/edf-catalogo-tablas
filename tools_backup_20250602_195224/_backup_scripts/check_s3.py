#!/usr/bin/env python3
"""
Script to verify S3 connection and bucket accessibility.
"""
import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get AWS S3 configuration from environment variables
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION')
    bucket_name = os.getenv('S3_BUCKET_NAME')
    
    # Check if required environment variables are set
    missing_vars = []
    if not aws_access_key:
        missing_vars.append('AWS_ACCESS_KEY_ID')
    if not aws_secret_key:
        missing_vars.append('AWS_SECRET_ACCESS_KEY')
    if not aws_region:
        missing_vars.append('AWS_REGION')
    if not bucket_name:
        missing_vars.append('S3_BUCKET_NAME')
    
    if missing_vars:
        print(f"❌ Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file.")
        sys.exit(1)
    
    print(f"AWS Region: {aws_region}")
    print(f"S3 Bucket: {bucket_name}")
    
    try:
        # Initialize S3 client
        print("\n📡 Connecting to AWS S3...")
        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        print("✅ S3 client successfully initialized")
        
        # Check if bucket exists and is accessible
        print(f"\n🔍 Checking if bucket '{bucket_name}' exists and is accessible...")
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' exists and is accessible")
        
        # List some objects in the bucket (if any)
        print("\n📋 Listing objects in bucket (up to 5)...")
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
        
        if 'Contents' in response:
            print(f"Found {len(response['Contents'])} objects:")
            for obj in response['Contents']:
                print(f"  - {obj['Key']} ({obj['Size']} bytes, last modified: {obj['LastModified']})")
        else:
            print("The bucket is empty.")
        
        print("\n✅ S3 connection test completed successfully!")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        print(f"❌ Error: {error_code}")
        print(f"Message: {error_message}")
        
        if error_code == '403':
            print("\nPossible causes:")
            print("- Invalid AWS credentials")
            print("- The IAM user doesn't have sufficient permissions")
            print("- Bucket policy restricts access")
        elif error_code == '404':
            print("\nPossible causes:")
            print("- The bucket doesn't exist")
            print("- You might have a typo in the bucket name")
        
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

