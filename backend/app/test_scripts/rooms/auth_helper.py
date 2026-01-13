#!/usr/bin/env python3
"""
Authentication Helper for Test Scripts

This module provides authentication functionality for test scripts by:
1. Reading test credentials from .env file
2. Logging into the API and obtaining access tokens
3. Providing authenticated session objects for other tests

Usage:
    from auth_helper import get_authenticated_session, get_access_token

    # Get authenticated requests session
    session = get_authenticated_session()
    response = session.get("http://localhost:8000/api/users/me")

    # Or just get the token
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

Requirements:
    - .env file in backend/ directory with TEST_USER_EMAIL and TEST_USER_PASSWORD
    - Backend server running on localhost:8000
    - Test user account created in database
"""

import sys
from pathlib import Path

import requests

# Add parent directory to path to import from backend
sys.path.append(str(Path(__file__)))

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/v1/login/access-token"
TEST_TOKEN_ENDPOINT = f"{BASE_URL}/api/v1/login/test-token"

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass

class AuthHelper:
    """Manages authentication for test scripts"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.access_token: str | None = None
        self._load_credentials()

    def _load_credentials(self):
        """Load test credentials from .env file"""
        # Look for test.env in the test-scripts directory first
        script_dir = Path(__file__).parent
        env_path = script_dir / "test.env"

        # If not found in test-scripts, look in parent app directory
        if not env_path.exists():
            env_path = script_dir.parent / "test.env"

        # If still not found, look in the backend root directory
        if not env_path.exists():
            env_path = script_dir.parent.parent / "test.env"

        if not env_path.exists():
            raise AuthenticationError(
                f"❌ test.env file not found in any of these locations:\n"
                f"   - {script_dir / 'test.env'}\n"
                f"   - {script_dir.parent / 'test.env'}\n"
                f"   - {script_dir.parent.parent / 'test.env'}\n"
                "Please create test.env file with TEST_USER_EMAIL and TEST_USER_PASSWORD"
            )

        # Simple .env parsing
        env_vars = {}
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')

        self.test_email = env_vars.get('TEST_USER_EMAIL')
        self.test_password = env_vars.get('TEST_USER_PASSWORD')

        if not self.test_email or not self.test_password:
            raise AuthenticationError(
                "❌ Missing TEST_USER_EMAIL or TEST_USER_PASSWORD in .env file\n"
                "Please add:\n"
                "TEST_USER_EMAIL=test@example.com\n"
                "TEST_USER_PASSWORD=your_password"
            )

    def login(self) -> str:
        """
        Login to API and get access token

        Returns:
            str: Access token for API requests

        Raises:
            AuthenticationError: If login fails
        """
        print(f"🔐 Attempting login for {self.test_email}...")

        # Prepare login data (OAuth2PasswordRequestForm format)
        login_data = {
            "username": self.test_email,  # FastAPI OAuth2 uses 'username' field
            "password": self.test_password
        }

        try:
            response = requests.post(
                LOGIN_ENDPOINT,
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                print("✅ Login successful! Token obtained.")
                return self.access_token

            elif response.status_code == 400:
                error_detail = response.json().get("detail", "Unknown error")
                raise AuthenticationError(f"❌ Login failed: {error_detail}")

            else:
                raise AuthenticationError(
                    f"❌ Login failed with status {response.status_code}: {response.text}"
                )

        except requests.exceptions.ConnectionError:
            raise AuthenticationError(
                f"❌ Cannot connect to server at {self.base_url}\n"
                "Please ensure the backend server is running."
            )
        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"❌ Request failed: {e}")

    def test_token(self) -> dict:
        """
        Test the current access token by calling test-token endpoint

        Returns:
            dict: User information if token is valid

        Raises:
            AuthenticationError: If token is invalid
        """
        if not self.access_token:
            raise AuthenticationError("❌ No access token. Call login() first.")

        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            response = requests.post(TEST_TOKEN_ENDPOINT, headers=headers)

            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Token valid for user: {user_data.get('email', 'Unknown')}")
                return user_data
            else:
                raise AuthenticationError(
                    f"❌ Token validation failed: {response.status_code} - {response.text}"
                )

        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"❌ Token test failed: {e}")

    def get_authenticated_session(self) -> requests.Session:
        """
        Get a requests.Session object with authentication headers set

        Returns:
            requests.Session: Session with Authorization header
        """
        if not self.access_token:
            self.login()

        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        })

        return session

    def get_headers(self) -> dict:
        """
        Get authentication headers for manual requests

        Returns:
            dict: Headers with Authorization and Content-Type
        """
        if not self.access_token:
            self.login()

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

# Global instance for convenience
_auth_helper = None

def get_auth_helper() -> AuthHelper:
    """Get global AuthHelper instance"""
    global _auth_helper
    if _auth_helper is None:
        _auth_helper = AuthHelper()
    return _auth_helper

def get_access_token() -> str:
    """Convenience function to get access token"""
    helper = get_auth_helper()
    if not helper.access_token:
        helper.login()
    return helper.access_token

def get_authenticated_session() -> requests.Session:
    """Convenience function to get authenticated session"""
    return get_auth_helper().get_authenticated_session()

def get_auth_headers() -> dict:
    """Convenience function to get auth headers"""
    return get_auth_helper().get_headers()

def test_authentication():
    """Test the authentication flow"""
    print("🧪 Testing Authentication Flow")
    print("=" * 50)

    try:
        # Initialize auth helper
        helper = AuthHelper()
        print(f"📧 Test user email: {helper.test_email}")

        # Login
        token = helper.login()
        print(f"🔑 Access token: {token[:20]}...{token[-10:] if len(token) > 30 else ''}")

        # Test token
        user_data = helper.test_token()
        print(f"👤 User info: {user_data.get('full_name', 'N/A')} ({user_data.get('email', 'N/A')})")
        print(f"🔒 Is superuser: {user_data.get('is_superuser', False)}")

        # Test authenticated session
        session = helper.get_authenticated_session()
        response = session.get(f"{BASE_URL}/api/v1/users/me")
        if response.status_code == 200:
            print("✅ Authenticated session working")
        else:
            print(f"❌ Authenticated session failed: {response.status_code}")

        print()
        print("🎉 Authentication test completed successfully!")
        print()
        print("💡 Usage in other scripts:")
        print("   from auth_helper import get_authenticated_session")
        print("   session = get_authenticated_session()")
        print("   response = session.get('http://localhost:8000/api/master-templates')")

        return True

    except AuthenticationError as e:
        print("\n❌ Authentication test failed:")
        print(f"   {e}")
        print()
        print("🔧 Troubleshooting steps:")
        print("   1. Check .env file exists with TEST_USER_EMAIL and TEST_USER_PASSWORD")
        print("   2. Verify backend server is running on localhost:8000")
        print("   3. Confirm test user account exists in database")
        print("   4. Check user credentials are correct")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Run authentication test when script is executed directly
    success = test_authentication()
    sys.exit(0 if success else 1)
