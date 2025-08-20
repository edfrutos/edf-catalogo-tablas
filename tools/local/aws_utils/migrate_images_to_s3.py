#!/usr/bin/env python3
"""
Script to migrate images from local filesystem to Amazon S3.
This script will:
1. Connect to MongoDB and retrieve all records with images
2. For each image, check if it exists in the filesystem
3. Upload existing images to S3
4. Update the MongoDB records with the new S3 paths
5. Print migration statistics
"""

import os
import secrets
import sys
import time
from pathlib import Path

import boto3
import certifi
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables from .env file
load_dotenv()

# Configure SSL certificate file for secure connections
os.environ['SSL_CERT_FILE'] = certifi.where()
# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("Error: MONGO_URI environment variable not set")
    sys.exit(1)

# AWS S3 configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME]):
    print("Error: One or more AWS environment variables not set")
    print("Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME")
    sys.exit(1)

# Connect to MongoDB
try:
    client = MongoClient(MONGO_URI)
    db = client["app_catalogojoyero_nueva"]  # Database name from app.py
    catalog_collection = db["67b8c24a7fdc72dd4d8703cf"]  # Collection name from app.py
    print(f"Connected to MongoDB: {client.server_info()['version']}")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    sys.exit(1)

# Initialize S3 client
try:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    print(f"Connected to AWS S3 in region {AWS_REGION}")
except ClientError as e:
    print(f"Error connecting to AWS S3: {e}")
    sys.exit(1)

# Path to the uploaded images directory
UPLOAD_FOLDER = Path("imagenes_subidas")
if not UPLOAD_FOLDER.exists():
    print(f"Error: Directory {UPLOAD_FOLDER} does not exist")
    sys.exit(1)

def upload_file_to_s3(file_path, object_name=None):
    """Upload a file to an S3 bucket
    
    Args:
        file_path (str): Path to the file to upload
        object_name (str, optional): S3 object name. If not provided, file_path's basename is used
        
    Returns:
        bool: True if file was uploaded, else False
    """
    if object_name is None:
        object_name = os.path.basename(file_path)

    try:
        s3_client.upload_file(file_path, S3_BUCKET_NAME, object_name)
        return True
    except ClientError as e:
        print(f"Error uploading file {file_path} to S3: {e}")
        return False

def migrate_images():
    """Migrate all images from local filesystem to S3"""
    # Statistics
    total_records = 0
    records_with_images = 0
    total_images = 0
    images_migrated = 0
    images_failed = 0
    images_not_found = 0

    print(f"Starting migration of images to S3 bucket: {S3_BUCKET_NAME}")

    # Find all records with images
    query = {"Imagenes": {"$exists": True, "$ne": [None, None, None]}}
    records = catalog_collection.find(query)

    total_records = catalog_collection.count_documents({})
    records_with_images = catalog_collection.count_documents(query)

    print(f"Found {records_with_images} records with images out of {total_records} total records")

    # Process each record
    for record in records:
        record_id = record.get("_id")
        images = record.get("Imagenes", [])

        # Skip records without images
        if not images:
            continue

        print(f"\nProcessing record {record_id}:")

        # Process each image in the record
        for i, image_path in enumerate(images):
            if not image_path:
                continue

            total_images += 1

            # Check if image path is already in S3 format
            if image_path.startswith("s3://"):
                print(f"  Image {i+1} already in S3 format: {image_path}")
                continue

            # Extract filename from the image path
            if image_path.startswith("/"):
                image_path = image_path[1:]  # Remove leading slash

            filename = os.path.basename(image_path)
            local_file_path = UPLOAD_FOLDER / filename

            print(f"  Processing image {i+1}: {filename}")

            # Check if file exists
            if not local_file_path.exists():
                print(f"    File not found: {local_file_path}")
                images_not_found += 1
                continue

            # Generate a unique filename to avoid collisions
            timestamp = int(time.time())
            random_suffix = secrets.token_hex(4)
            unique_filename = f"{timestamp}_{random_suffix}_{filename}"

            # Upload file to S3
            print(f"    Uploading to S3 as: {unique_filename}")
            if upload_file_to_s3(str(local_file_path), unique_filename):
                # Update MongoDB record with S3 path
                s3_path = f"s3://{S3_BUCKET_NAME}/{unique_filename}"
                catalog_collection.update_one(
                    {"_id": record_id},
                    {"$set": {f"Imagenes.{i}": s3_path}}
                )
                print(f"    ✅ Successfully migrated to: {s3_path}")
                images_migrated += 1
            else:
                print(f"    ❌ Failed to upload {filename} to S3")
                images_failed += 1

    # Print statistics
    print("\n" + "="*50)
    print("MIGRATION STATISTICS")
    print("="*50)
    print(f"Total records: {total_records}")
    print(f"Records with images: {records_with_images}")
    print(f"Total images processed: {total_images}")
    print(f"Images successfully migrated: {images_migrated}")
    print(f"Images not found in filesystem: {images_not_found}")
    print(f"Images failed to upload: {images_failed}")
    print("="*50)

    if images_migrated + images_not_found + images_failed == total_images:
        print("✅ Migration completed successfully")
    else:
        print("⚠️ Migration completed with inconsistencies")

if __name__ == "__main__":
    migrate_images()

