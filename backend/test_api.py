#!/usr/bin/env python3
"""
Simple script to test the Django REST API endpoints
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_login():
    """Test login endpoint"""
    print("\n1. Testing Login Endpoint...")
    url = f"{BASE_URL}/api/auth/login/"
    data = {"username": "owner", "password": "owner123"}
    
    try:
        response = requests.post(url, json=data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Token: {result.get('token')[:20]}...")
            print(f"   User: {result.get('user', {}).get('username')}")
            print(f"   Role: {result.get('user', {}).get('role')}")
            return result.get('token')
        else:
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"   Exception: {e}")
        return None

def test_products(token):
    """Test products endpoint"""
    print("\n2. Testing Products List...")
    url = f"{BASE_URL}/api/inventory/products/"
    headers = {"Authorization": f"Token {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Total Products: {result.get('count')}")
            products = result.get('results', [])
            for p in products[:3]:
                print(f"   - {p['name']} ({p['sku']}): {p['selling_price']} RWF, Stock: {p['quantity_in_stock']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")

def test_categories(token):
    """Test categories endpoint"""
    print("\n3. Testing Categories List...")
    url = f"{BASE_URL}/api/inventory/categories/"
    headers = {"Authorization": f"Token {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Total Categories: {result.get('count')}")
            for cat in result.get('results', []):
                print(f"   - {cat['name']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")

def test_agents(token):
    """Test agents endpoint"""
    print("\n4. Testing Agents List...")
    url = f"{BASE_URL}/api/agents/agents/"
    headers = {"Authorization": f"Token {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Total Agents: {result.get('count')}")
            for agent in result.get('results', []):
                print(f"   - {agent['full_name']} ({agent['area']}): Debt={agent['total_debt']} RWF")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")

def test_low_stock(token):
    """Test low stock endpoint"""
    print("\n5. Testing Low Stock Products...")
    url = f"{BASE_URL}/api/inventory/products/low_stock/"
    headers = {"Authorization": f"Token {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Low Stock Items: {len(result)}")
            for p in result:
                print(f"   - {p['name']}: Stock={p['quantity_in_stock']}, Reorder Level={p['reorder_level']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")

def main():
    print("=" * 50)
    print("EROM System API Tests")
    print("=" * 50)
    
    # Test login first
    token = test_login()
    
    if token:
        # Test other endpoints
        test_categories(token)
        test_products(token)
        test_agents(token)
        test_low_stock(token)
        
        print("\n" + "=" * 50)
        print("✓ All API tests completed!")
        print("=" * 50)
    else:
        print("\n✗ Login failed - cannot proceed with other tests")

if __name__ == "__main__":
    main()
