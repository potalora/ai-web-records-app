#!/usr/bin/env python3
import requests
import time

# First register a user
register_data = {
    "email": f"logintest{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "firstName": "Login",
    "lastName": "Test", 
    "dateOfBirth": "1990-01-01",
    "phone": "5551234567",
    "acceptTerms": True,
    "acceptPrivacy": True
}

print("Registering user...")
register_response = requests.post("http://localhost:8000/auth/register", json=register_data)
print(f"Registration Status: {register_response.status_code}")
print(f"Registration Response: {register_response.text}")

if register_response.status_code == 200:
    # Now test login
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }
    
    print("\nTesting login...")
    login_response = requests.post("http://localhost:8000/auth/login", json=login_data)
    print(f"Login Status: {login_response.status_code}")
    print(f"Login Response: {login_response.text}")
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        token = login_result["token"]
        
        # Test session validation
        print("\nTesting session validation...")
        headers = {"Authorization": f"Bearer {token}"}
        session_response = requests.get("http://localhost:8000/auth/session/validate", headers=headers)
        print(f"Session Validation Status: {session_response.status_code}")
        print(f"Session Validation Response: {session_response.text}")
else:
    print("Registration failed, cannot test login")