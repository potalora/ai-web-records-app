#!/usr/bin/env python3
import requests
import time

# First register and login to get a token
register_data = {
    "email": f"dashtest{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "firstName": "Dashboard",
    "lastName": "Test", 
    "dateOfBirth": "1990-01-01",
    "phone": "5551234567",
    "acceptTerms": True,
    "acceptPrivacy": True
}

print("Registering user for dashboard testing...")
register_response = requests.post("http://localhost:8000/auth/register", json=register_data)
print(f"Registration Status: {register_response.status_code}")

if register_response.status_code == 200:
    login_result = register_response.json()
    token = login_result["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test dashboard endpoints
    endpoints = [
        "/dashboard/stats",
        "/dashboard/recent-uploads", 
        "/dashboard/health-summary"
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint}...")
        response = requests.get(f"http://localhost:8000{endpoint}", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
else:
    print(f"Registration failed: {register_response.text}")