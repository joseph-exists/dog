"""
Forgejo API Client Configuration

Shared client setup for all Typer commands. Uses the local openapi_client in app/lib/.

Usage:
    from forge_client import get_api_client, get_admin_api, get_user_api

    admin = get_admin_api()
    user = admin.admin_create_user(body=CreateUserOption(...))

Note:
    Path setup is handled by main.py - this module assumes app.lib.openapi_client
    is already importable. Always run via main.py, not directly.
"""
import openapi_client
from openapi_client import (
    AdminApi,
    IssueApi,
    OrganizationApi,
    RepositoryApi,
    UserApi,
)

# =============================================================================
# Configuration
# =============================================================================

FORGE_URL = "http://localhost:3000/api/v1"

# Token configuration
# Admin token (forge-test user): 63d42c1df2b231be68209d45739f14732f06eaba
# Claude token: 4b0f449a6dcf184b0ee94a1fcb0c8b768ca8b779

#  Claude's token
# API_TOKEN = "4b0f449a6dcf184b0ee94a1fcb0c8b768ca8b779"
# admin token
# API_TOKEN= "63d42c1df2b231be68209d45739f14732f06eaba"
# shadowusers token
# API_TOKEN="e735f46ad918c9b9e0d4afc84f8b9191b1e43a23"
# SHADOW_AGENTS_TOKEN="13089e081cd56a305978b7ea885fcd6321d31607"
# SHADOW_STORIES_TOKEN="f0a4447afb19261890f9810619c14eb87d58cae8"
# SHADOW_ROOMS_TOKEN="4a43adac1520a904e357b8772718e2217ebbc5e6"
# SHADOW_PERSONAS_TOKEN="1b907d8d816cc7dafdab6cc66af4e939490be4ac"
# SHADOW_LLM_MODELS_TOKEN="1b1999a941afac74a1db9d42600e307a4e15eb66"
# SHADOW_USER_LLM_PROVIDERS_TOKEN="b2812c6096cbde3647d2c1016a613da6951f58b1"
# SHADOW_PROMPTS_TOKEN="ec085a5f80ddcaef323b43d3cd30fe8d3f84d876"
# API_TOKEN="ec085a5f80ddcaef323b43d3cd30fe8d3f84d876"
API_TOKEN = "13089e081cd56a305978b7ea885fcd6321d31607"

# =============================================================================
# Client Factory
# =============================================================================

_api_client: openapi_client.ApiClient | None = None


def get_api_client() -> openapi_client.ApiClient:
    """Get or create the shared API client instance."""
    global _api_client

    if _api_client is None:
        config = openapi_client.Configuration(host=FORGE_URL)
        config.api_key["AuthorizationHeaderToken"] = API_TOKEN
        config.api_key_prefix["AuthorizationHeaderToken"] = "token"
        _api_client = openapi_client.ApiClient(config)

    return _api_client


def get_admin_api() -> AdminApi:
    """Get AdminApi instance for admin operations."""
    return AdminApi(get_api_client())


def get_user_api() -> UserApi:
    """Get UserApi instance for user operations."""
    return UserApi(get_api_client())


def get_repository_api() -> RepositoryApi:
    """Get RepositoryApi instance for repository operations."""
    return RepositoryApi(get_api_client())


def get_organization_api() -> OrganizationApi:
    """Get OrganizationApi instance for organization operations."""
    return OrganizationApi(get_api_client())


def get_issue_api() -> IssueApi:
    """Get IssueApi instance for issue operations."""
    return IssueApi(get_api_client())


# =============================================================================
# Utility Functions
# =============================================================================

def get_current_user() -> dict:
    """Get the currently authenticated user."""
    user_api = get_user_api()
    return user_api.user_get_current().to_dict()


def test_connection() -> bool:
    """Test if the API connection works."""
    try:
        user = get_current_user()
        return user is not None
    except Exception:
        return False


# =============================================================================
# CLI Test
# =============================================================================

if __name__ == "__main__":
    print(f"Testing connection to {FORGE_URL}...")
    print(f"Token: {API_TOKEN[:8]}...{API_TOKEN[-4:]}")

    try:
        user = get_current_user()
        print(f"✅ Connected as: {user.get('login')} ({user.get('email')})")
        print(f"   Is Admin: {user.get('is_admin')}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
