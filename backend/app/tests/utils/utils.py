import logging
import random
import string

from fastapi.testclient import TestClient

from app.core.config import settings

logger = logging.getLogger(__name__)


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def get_superuser_token_headers(client: TestClient) -> dict[str, str]:
    if not settings.FIRST_SUPERTESTUSER or not settings.FIRST_SUPERTESTUSER_PASSWORD:
        logger.error("Missing superuser credentials in settings")
        raise ValueError(
            "FIRST_SUPERTESTUSER and FIRST_SUPERTESTUSER_PASSWORD must be set in .env file"
        )

    logger.info(f"Attempting to login with email: {settings.FIRST_SUPERTESTUSER}")

    login_data = {
        "username": settings.FIRST_SUPERTESTUSER,
        "password": settings.FIRST_SUPERTESTUSER_PASSWORD,
    }
    logger.debug(f"Login request data: {login_data}")

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    logger.debug(f"Login response status: {r.status_code}")
    logger.debug(f"Login response body: {r.text}")

    if r.status_code != 200:
        logger.error(f"Login failed. Status: {r.status_code}, Response: {r.text}")
        raise ValueError(
            f"Failed to get superuser token. Status code: {r.status_code}, "
            f"Response: {r.text}"
        )

    tokens = r.json()
    if "access_token" not in tokens:
        logger.error(f"Invalid response format: {tokens}")
        raise ValueError(
            f"Invalid response format. Expected access_token, got: {tokens}"
        )

    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    logger.info("Successfully obtained superuser token")
    return headers
