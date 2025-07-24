#!/usr/bin/env python3
import requests
import time

data = {
    "email": f"quicktest{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "firstName": "Quick",
    "lastName": "Test", 
    "dateOfBirth": "1990-01-01",
    "phone": "5551234567",
    "acceptTerms": True,
    "acceptPrivacy": True
}

response = requests.post("http://localhost:8000/auth/register", json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")