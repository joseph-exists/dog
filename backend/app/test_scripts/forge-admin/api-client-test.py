#!/usr/bin/env python3
"""
Test script for Forgejo API client - Create a test user

Usage:
    python api-client-test.py
"""

import sys
from pathlib import Path
from pprint import pprint

# Add the forge-sdk to the path
SDK_PATH = Path.home() / "dog" / "forge-sdk" / "python-sdk"
sys.path.insert(0, str(SDK_PATH))

import openapi_client
from openapi_client.api.admin_api import AdminApi
from openapi_client.api.user_api import UserApi
from openapi_client.models.create_user_option import CreateUserOption
from openapi_client.rest import ApiException

# Configuration
FORGE_URL = "http://localhost:3000/api/v1"
# Admin-level token with full admin privileges (write:admin scope)
API_TOKEN = "63d42c1df2b231be68209d45739f14732f06eaba"


def get_api_client() -> openapi_client.ApiClient:
    """Create and return configured API client"""
    print("=" * 60)
    print("🔧 CONFIGURING API CLIENT")
    print("=" * 60)
    print(f"   Host URL: {FORGE_URL}")
    print(f"   Token: {API_TOKEN[:8]}...{API_TOKEN[-4:]}")

    config = openapi_client.Configuration(host=FORGE_URL)
    config.api_key["AuthorizationHeaderToken"] = API_TOKEN
    config.api_key_prefix["AuthorizationHeaderToken"] = "token"

    print(f"   Auth header will be: 'token {API_TOKEN[:8]}...'")
    print()

    return openapi_client.ApiClient(config)


def verify_authentication(api_client: openapi_client.ApiClient) -> dict | None:
    """Verify token works by getting current user info"""
    print("=" * 60)
    print("🔐 VERIFYING AUTHENTICATION")
    print("=" * 60)

    user_api = UserApi(api_client)

    try:
        print("   Calling: GET /user (user_get_current)")
        current_user = user_api.user_get_current()
        user_dict = current_user.to_dict()

        print(f"   ✅ Authenticated as: {user_dict.get('login')}")
        print(f"   Email: {user_dict.get('email')}")
        print(f"   Is Admin: {user_dict.get('is_admin')}")
        print(f"   User ID: {user_dict.get('id')}")
        print()
        return user_dict

    except ApiException as e:
        print(f"   ❌ Auth verification failed: {e.status} - {e.reason}")
        print(f"   Body: {e.body}")
        print()
        return None


def check_admin_access(api_client: openapi_client.ApiClient) -> bool:
    """Test if we have admin read access by listing emails"""
    print("=" * 60)
    print("🔑 CHECKING ADMIN ACCESS (read:admin)")
    print("=" * 60)

    admin_api = AdminApi(api_client)

    try:
        print("   Calling: GET /admin/emails (admin_get_all_emails)")
        emails = admin_api.admin_get_all_emails(limit=1)
        print(f"   ✅ Admin read access confirmed (found {len(emails)} email(s))")
        print()
        return True

    except ApiException as e:
        print(f"   ❌ Admin read failed: {e.status} - {e.reason}")
        print(f"   Body: {e.body}")
        print()
        return False


def create_test_user(
    api_client: openapi_client.ApiClient,
    username: str,
    email: str,
    password: str,
    full_name: str | None = None,
) -> dict:
    """Create a new user via Forgejo Admin API"""
    print("=" * 60)
    print("👤 CREATING TEST USER (write:admin)")
    print("=" * 60)

    admin_api = AdminApi(api_client)

    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Full name: {full_name or username}")
    print()

    user_options = CreateUserOption(
        username=username,
        email=email,
        password=password,
        full_name=full_name or username,
        must_change_password=False,
        send_notify=False,
    )

    print("   CreateUserOption payload:")
    pprint(user_options.to_dict(), indent=6)
    print()

    try:
        print("   Calling: POST /admin/users (admin_create_user)")
        user = admin_api.admin_create_user(body=user_options)
        print(f"   ✅ User created successfully!")
        print()
        return user.to_dict()

    except ApiException as e:
        print(f"   ❌ Failed to create user: {e.status} - {e.reason}")
        print(f"   Response body: {e.body}")
        print()
        raise


def main():
    """Main test flow"""
    print()
    print("🚀 FORGEJO API CLIENT TEST")
    print("=" * 60)
    print()

    # Step 1: Create API client
    api_client = get_api_client()

    # Step 2: Verify authentication
    current_user = verify_authentication(api_client)
    if not current_user:
        print("❌ Cannot proceed - authentication failed")
        sys.exit(1)

    # Step 3: Check admin read access
    has_admin_read = check_admin_access(api_client)
    if not has_admin_read:
        print("⚠️  Warning: No admin read access, write access likely missing too")

    # Step 4: Try to create user
    test_user = {
        "username": "apitest1",
        "email": "apitest1@test.local",
        "password": "testpassword123",
        "full_name": "API Test User",
    }

    try:
        result = create_test_user(api_client, **test_user)
        print("=" * 60)
        print("✅ SUCCESS - Created user details:")
        print("=" * 60)
        pprint(result)

    except ApiException as e:
        print("=" * 60)
        print("❌ FAILED - Error details:")
        print("=" * 60)
        if e.status == 422:
            print("   User may already exist (422 Unprocessable Entity)")
        elif e.status == 403:
            print("   Token missing required scope: write:admin")
            print("   Create a new token with 'Administrator: Read and Write' permission")
        sys.exit(1)


if __name__ == "__main__":
    main()
