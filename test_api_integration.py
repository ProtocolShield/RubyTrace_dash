#!/usr/bin/env python3
"""
Test script to verify the new API integration functionality.
"""

import requests
import json
import sys

# Base URL for the API
BASE_URL = "http://localhost:5000"

def test_api_integration():
    """Test the new API integration endpoints."""
    
    print("Testing API Integration Endpoints...")
    print("=" * 50)
    
    # Test 1: Get integrated APIs (should be empty initially)
    print("\n1. Testing GET /api/config/integrated_apis")
    try:
        response = requests.get(f"{BASE_URL}/api/config/integrated_apis")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✓ GET integrated_apis endpoint working")
        else:
            print("✗ GET integrated_apis endpoint failed")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Test API integration
    print("\n2. Testing POST /api/config/integrate_api")
    test_api_data = {
        "service": "test_api_service",
        "key": "test_api_key_12345",
        "api_type": "breach",
        "endpoint_url": "https://api.testservice.com/v1/breaches",
        "refresh_interval": 30,
        "priority": "medium",
        "enabled": True,
        "metadata": {"description": "Test API integration"}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/config/integrate_api",
            json=test_api_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get("success"):
                print("✓ API integration successful")
            else:
                print("✗ API integration failed")
        else:
            print("✗ API integration endpoint failed")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Verify the API was added
    print("\n3. Verifying API was added")
    try:
        response = requests.get(f"{BASE_URL}/api/config/integrated_apis")
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "test_api_service" in data.get("integrated_apis", {}):
                print("✓ API successfully integrated and visible")
                print(f"Integrated APIs: {list(data['integrated_apis'].keys())}")
            else:
                print("✗ API not found in integrated list")
        else:
            print("✗ Failed to verify API integration")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 4: Test API key management
    print("\n4. Testing API key management")
    try:
        response = requests.get(f"{BASE_URL}/api/config/api_keys")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"API Keys: {json.dumps(data, indent=2)}")
            print("✓ API key management working")
        else:
            print("✗ API key management failed")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 50)
    print("API Integration Test Completed")

if __name__ == "__main__":
    print("Make sure the API server is running on http://localhost:5000")
    print("Starting API integration tests...")
    test_api_integration()
