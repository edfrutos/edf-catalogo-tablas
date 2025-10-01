#!/usr/bin/env python3
import os

import boto3
from dotenv import load_dotenv


def list_s3_buckets():
    """
    List all S3 buckets available to the configured AWS credentials.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Print AWS region for reference
    region = os.getenv("AWS_REGION")
    print(f"AWS Region: {region}")

    try:
        # Create an S3 client
        s3_client = boto3.client("s3")

        # Get list of buckets
        response = s3_client.list_buckets()

        # Print bucket information
        print("\nBuckets available:")
        if "Buckets" in response and response["Buckets"]:
            for bucket in response["Buckets"]:
                print(f" - {bucket['Name']}")

                # Try to get bucket location
                try:
                    location = s3_client.get_bucket_location(Bucket=bucket["Name"])
                    # None means us-east-1
                    region = location["LocationConstraint"] or "us-east-1"
                    print(f"   Region: {region}")
                except Exception as e:
                    print(f"   Unable to get region: {str(e)}")

            print(f"\nTotal buckets: {len(response['Buckets'])}")
        else:
            print("No buckets found for these credentials.")

    except Exception as e:
        print(f"\nError accessing S3: {str(e)}")
        print("\nPlease check your AWS credentials in the .env file.")
        print(
            "Make sure your AWS user has the necessary permissions (s3:ListAllMyBuckets)."
        )


if __name__ == "__main__":
    list_s3_buckets()
