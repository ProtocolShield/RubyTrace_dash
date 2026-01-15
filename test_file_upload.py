#!/usr/bin/env python3
"""
Test script to verify the file upload functionality.
"""

import requests
import json
import os
import sys
from pathlib import Path

# Base URL for the API
BASE_URL = "http://localhost:5000"

def test_file_upload():
    """Test the file upload functionality."""

    print("Testing File Upload System...")
    print("=" * 50)

    # Test 1: Upload a test file
    print("\n1. Testing file upload")
    test_file_path = "test_upload.csv"

    if not os.path.exists(test_file_path):
        print(f"✗ Test file {test_file_path} not found")
        return

    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_upload.csv', f, 'text/csv')}
            data = {'uploader_id': '1', 'is_public': 'false'}

            response = requests.post(
                f"{BASE_URL}/api/uploads",
                files=files,
                data=data
            )

        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get("success"):
                print("✓ File upload successful")
                upload_result = data.get("upload_result", {})
                upload_id = upload_result.get("upload_id")
                print(f"✓ Upload ID: {upload_id}")
            else:
                print("✗ File upload failed")
                print(f"Error: {data.get('error')}")
                return
        else:
            print("✗ File upload endpoint failed")
            print(f"Response: {response.text}")
            return

    except Exception as e:
        print(f"✗ Error: {e}")
        return

    # Test 2: List uploads
    print("\n2. Testing upload listing")
    try:
        response = requests.get(f"{BASE_URL}/api/uploads")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get("success") and data.get("uploads"):
                print("✓ Upload listing successful")
                uploads = data.get("uploads", [])
                print(f"✓ Found {len(uploads)} uploads")

                # Find our uploaded file
                our_upload = None
                for upload in uploads:
                    if upload.get("filename") == "test_upload.csv":
                        our_upload = upload
                        break

                if our_upload:
                    print("✓ Our uploaded file found in list")
                    print(f"  - Risk Level: {our_upload.get('risk_level')}")
                    print(f"  - Storage Status: {our_upload.get('storage_status')}")
                    print(f"  - Uploaded At: {our_upload.get('uploaded_at')}")
                else:
                    print("✗ Our uploaded file not found in list")
            else:
                print("✗ No uploads found or listing failed")
        else:
            print("✗ Upload listing endpoint failed")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 3: Get upload details
    if upload_id:
        print(f"\n3. Testing upload details for ID: {upload_id}")
        try:
            response = requests.get(f"{BASE_URL}/api/uploads/{upload_id}")
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                if data.get("success"):
                    print("✓ Upload details retrieved successfully")
                    upload = data.get("upload", {})
                    print(f"  - Filename: {upload.get('filename')}")
                    print(f"  - Risk Level: {upload.get('risk_level')}")
                    print(f"  - Partial Content Length: {len(upload.get('partial_content', ''))}")
                    print(f"  - Scan Result: {upload.get('scan_result', {}).get('risk_assessment', {}).get('level')}")
                else:
                    print("✗ Upload details retrieval failed")
            else:
                print("✗ Upload details endpoint failed")
        except Exception as e:
            print(f"✗ Error: {e}")

    # Test 4: Test filtering by risk level
    print("\n4. Testing risk level filtering")
    try:
        response = requests.get(f"{BASE_URL}/api/uploads?risk_level=medium")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                uploads = data.get("uploads", [])
                print(f"✓ Found {len(uploads)} uploads with medium risk")
                print("✓ Risk level filtering working")
            else:
                print("✗ Risk level filtering failed")
        else:
            print("✗ Risk level filtering endpoint failed")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 5: Test download (if file is not quarantined)
    if upload_id and our_upload and our_upload.get('storage_status') != 'quarantined':
        print(f"\n5. Testing file download for ID: {upload_id}")
        try:
            response = requests.get(f"{BASE_URL}/api/uploads/{upload_id}/download")
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("✓ File download successful")
                print(f"  - Content Length: {len(response.content)} bytes")
                print(f"  - Content Type: {response.headers.get('content-type')}")
            else:
                print("✗ File download failed")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"✗ Error: {e}")

    print("\n" + "=" * 50)
    print("File Upload Test Completed")

    # Cleanup
    if os.path.exists(test_file_path):
        print(f"\nCleaning up test file: {test_file_path}")
        os.remove(test_file_path)

if __name__ == "__main__":
    print("Make sure the API server is running on http://localhost:5000")
    print("Starting file upload tests...")
    test_file_upload()
