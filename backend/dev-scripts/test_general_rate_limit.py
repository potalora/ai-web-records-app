#!/usr/bin/env python3
"""
Test rate limiting on general endpoints (non-health).
"""
import requests
import time

print("Testing rate limiting on general endpoints...")

# Test rate limiting on /models endpoint
for i in range(65):  # Over the 60/min limit
    try:
        response = requests.get("http://localhost:8000/models/")
        if response.status_code == 429:
            print(f"✓ Rate limiting triggered at request {i+1}")
            print(f"Response: {response.json()}")
            break
        elif i % 10 == 0:  # Show progress every 10 requests
            print(f"Request {i+1}: {response.status_code}")
    except Exception as e:
        print(f"Request {i+1}: Error - {e}")
        break
else:
    print("Rate limiting not triggered within 65 requests")

print("Rate limiting test completed!")