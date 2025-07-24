#!/usr/bin/env python3
"""
Test security headers and rate limiting functionality.
"""
import requests
import time

print("Testing security features...")

# Test 1: Check security headers
print("\n1. Testing security headers...")
response = requests.get("http://localhost:8000/health")
print(f"Status: {response.status_code}")

security_headers = [
    "X-Content-Type-Options",
    "X-Frame-Options", 
    "X-XSS-Protection",
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "Referrer-Policy"
]

print("Security headers present:")
for header in security_headers:
    if header in response.headers:
        print(f"✓ {header}: {response.headers[header]}")
    else:
        print(f"✗ {header}: Missing")

# Test 2: Test rate limiting on auth endpoints
print("\n2. Testing rate limiting on auth endpoints...")
print("Making 12 rapid requests to /auth/session/validate (limit: 10/min)...")

for i in range(12):
    try:
        response = requests.get("http://localhost:8000/auth/session/validate")
        print(f"Request {i+1}: {response.status_code}")
        if response.status_code == 429:
            print(f"✓ Rate limiting triggered at request {i+1}")
            break
    except Exception as e:
        print(f"Request {i+1}: Error - {e}")
    time.sleep(0.1)

# Test 3: Test rate limiting on general endpoints
print("\n3. Testing rate limiting on general endpoints...")
print("Making rapid requests to /health...")

rate_limited = False
for i in range(65):  # Over the 60/min limit
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 429:
            print(f"✓ Rate limiting triggered at request {i+1}")
            rate_limited = True
            break
    except Exception as e:
        print(f"Request {i+1}: Error - {e}")
        break

if not rate_limited:
    print("Rate limiting not triggered (health endpoint may be excluded)")

print("\n✓ Security feature testing completed!")