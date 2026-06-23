"""
Simple test script to verify auth is working.
Run with: python test_auth_simple.py
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"


def test_login():
    """Test login endpoint"""
    print("Testing login...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "admin@college.edu",
            "password": "any-password"
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful!")
        print(f"Token: {data['access_token'][:50]}...")
        print(f"User: {data['user']['email']} ({data['user']['role']})")
        return data['access_token']
    else:
        print(f"❌ Login failed: {response.text}")
        return None


def test_me(token):
    """Test /auth/me endpoint"""
    print("\nTesting /auth/me...")
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ /auth/me successful!")
        print(f"User: {data['email']} ({data['role']})")
    else:
        print(f"❌ /auth/me failed: {response.text}")


def test_timetable(token):
    """Test /academic/timetable endpoint"""
    print("\nTesting /academic/timetable...")
    response = requests.get(
        f"{BASE_URL}/academic/timetable",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ /academic/timetable successful!")
        print(f"Entries: {len(data)}")
    else:
        print(f"❌ /academic/timetable failed: {response.text}")


if __name__ == "__main__":
    print("="*60)
    print("BACKEND AUTH TEST")
    print("="*60)
    print("Make sure backend is running on http://localhost:8000")
    print()
    
    token = test_login()
    if token:
        test_me(token)
        test_timetable(token)
    
    print("\n" + "="*60)
    print("DONE")
    print("="*60)
