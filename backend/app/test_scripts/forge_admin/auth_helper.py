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

# SHADOW_USERS_TOKEN="e735f46ad918c9b9e0d4afc84f8b9191b1e43a23"
# SHADOW_AGENTS_TOKEN="13089e081cd56a305978b7ea885fcd6321d31607"
# SHADOW_STORIES_TOKEN="f0a4447afb19261890f9810619c14eb87d58cae8"
# SHADOW_ROOMS_TOKEN="4a43adac1520a904e357b8772718e2217ebbc5e6"
# SHADOW_PERSONAS_TOKEN="1b907d8d816cc7dafdab6cc66af4e939490be4ac"
# SHADOW_LLM_MODELS_TOKEN="1b1999a941afac74a1db9d42600e307a4e15eb66"
# SHADOW_USER_LLM_PROVIDERS_TOKEN="b2812c6096cbde3647d2c1016a613da6951f58b1"
# SHADOW_PROMPTS_TOKEN="ec085a5f80ddcaef323b43d3cd30fe8d3f84d876"



import requests

# Configuration - edit these for your setup
BASE_URL = "http://localhost:3000/api/v1"
# current - shadow_agents
API_TOKEN = "13089e081cd56a305978b7ea885fcd6321d31607"
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
