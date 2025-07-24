#!/usr/bin/env python3
"""
Test AccessLog functionality for HIPAA compliance.
"""
import requests
import time
import io

# First register and login to get a token
register_data = {
    "email": f"accesstest{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "firstName": "Access",
    "lastName": "Test",
    "dateOfBirth": "1990-01-01",
    "phone": "5551234567",
    "acceptTerms": True,
    "acceptPrivacy": True
}

print("1. Registering user for access logging test...")
register_response = requests.post("http://localhost:8000/auth/register", json=register_data)
print(f"Registration Status: {register_response.status_code}")

if register_response.status_code == 200:
    login_result = register_response.json()
    token = login_result["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test file upload (should create AccessLog entry)
    print("\n2. Testing file upload with AccessLog...")
    test_content = "This is a test medical record for access logging."
    files = {
        'files': ('test_record.txt', io.BytesIO(test_content.encode()), 'text/plain')
    }
    data = {
        'upload_type': 'files',
        'title': 'Test Medical Record',
        'record_type': 'OTHER',
        'description': 'Test record for access logging'
    }
    
    upload_response = requests.post(
        "http://localhost:8000/ingest/files", 
        headers=headers, 
        files=files, 
        data=data
    )
    print(f"File Upload Status: {upload_response.status_code}")
    if upload_response.status_code == 200:
        print("✓ File uploaded successfully - AccessLog should be created")
    
    # Test dashboard endpoints (should create AccessLog entries)
    print("\n3. Testing dashboard endpoints with AccessLog...")
    
    dashboard_endpoints = [
        "/dashboard/health-summary",
        "/dashboard/medical-records"
    ]
    
    for endpoint in dashboard_endpoints:
        response = requests.get(f"http://localhost:8000{endpoint}", headers=headers)
        print(f"{endpoint}: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ {endpoint} accessed - AccessLog should be created")
    
    print("\n✓ Access logging test completed!")
    
else:
    print(f"Registration failed: {register_response.text}")