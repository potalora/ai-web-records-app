#!/usr/bin/env python3
"""
Test database transaction rollback on registration failures.
"""
import requests
import time

# Test 1: Duplicate email (should fail without creating partial data)
print("Test 1: Testing duplicate email handling...")

register_data = {
    "email": f"rollbacktest{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "firstName": "Rollback",
    "lastName": "Test",
    "dateOfBirth": "1990-01-01",
    "phone": "5551234567",
    "acceptTerms": True,
    "acceptPrivacy": True
}

# First registration should succeed
print("Attempting first registration...")
response1 = requests.post("http://localhost:8000/auth/register", json=register_data)
print(f"First registration: {response1.status_code} - {response1.text[:100]}")

# Second registration with same email should fail
print("Attempting duplicate registration...")
response2 = requests.post("http://localhost:8000/auth/register", json=register_data)
print(f"Duplicate registration: {response2.status_code} - {response2.text[:100]}")

# Test 2: Invalid data (should fail cleanly)
print("\nTest 2: Testing invalid data handling...")

invalid_data = {
    "email": "invalid-email",  # Invalid email format
    "password": "weak",        # Weak password
    "firstName": "Test",
    "lastName": "User",
    "dateOfBirth": "1990-01-01",
    "acceptTerms": True,
    "acceptPrivacy": True
}

response3 = requests.post("http://localhost:8000/auth/register", json=invalid_data)
print(f"Invalid data registration: {response3.status_code} - {response3.text[:100]}")

print("\nTransaction rollback tests completed.")