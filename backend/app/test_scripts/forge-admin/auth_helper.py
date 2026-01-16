#!/usr/bin/env python3
"""
Forgejo API Helper for Test Scripts

Simple static token authentication for Forgejo API.
Forgejo uses: Authorization: token <api_token>

Usage:
    from auth_helper import get_session, get_headers, BASE_URL

    session = get_session()
    response = session.get(f"{BASE_URL}/user")

    # Or with raw requests
    response = requests.get(f"{BASE_URL}/user", headers=get_headers())
"""

import requests

# Configuration - edit these for your setup
BASE_URL = "http://localhost:3000/api/v1"
# this is an admin level 'read-write' token
API_TOKEN = "bed311c7b8d344456e1fdde5b9067cb7b8a45f43"
# this is an admin level token with user read/write privileges
# 444e92922536874d5f4c9ced20df5f11b5edf524
# repo read and write
# fe6b20bdac6f3466a1ef3233358ee4cdbb9cdcfc
# issue writer 
# bf7ddad5c4df450b09133c65ff43836a19ecc298

def get_headers() -> dict:
    """Get Forgejo auth headers"""
    return {
        "Authorization": f"token {API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def get_session() -> requests.Session:
    """Get authenticated requests session"""
    session = requests.Session()
    session.headers.update(get_headers())
    return session


def test_connection():
    """Quick test to verify API access"""
    print(f"Testing connection to {BASE_URL}...")

    try:
        response = requests.get(f"{BASE_URL}/user", headers=get_headers())

        if response.status_code == 200:
            user = response.json()
            print(f"✅ Connected as: {user.get('login')} ({user.get('email')})")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {BASE_URL}")
        return False


if __name__ == "__main__":
    test_connection()
