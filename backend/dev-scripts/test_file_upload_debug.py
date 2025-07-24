#!/usr/bin/env python3
"""
Debug file upload issues.
"""
import requests
import time
import io

# Register and get token
register_data = {
    "email": f"uploadtest{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "firstName": "Upload",
    "lastName": "Test",
    "dateOfBirth": "1990-01-01",
    "acceptTerms": True,
    "acceptPrivacy": True
}

register_response = requests.post("http://localhost:8000/auth/register", json=register_data)
if register_response.status_code == 200:
    token = register_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test file upload with detailed error info
    test_content = "This is a test medical record."
    files = {
        'files': ('test_record.txt', io.BytesIO(test_content.encode()), 'text/plain')
    }
    data = {
        'upload_type': 'files',
        'title': 'Test Record',
        'record_type': 'OTHER'
    }
    
    upload_response = requests.post(
        "http://localhost:8000/ingest/files", 
        headers=headers, 
        files=files, 
        data=data
    )
    print(f"Status: {upload_response.status_code}")
    print(f"Response: {upload_response.text}")
    
else:
    print("Registration failed")