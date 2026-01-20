from __future__ import annotations

from app.services.shadow_summaries import summarize_user_llm_provider


def test_summarize_user_llm_provider_redacts_keys() -> None:
    snapshot = {
        "user_llm_provider": {
            "id": "provider-id",
            "user_id": "user-id",
            "provider_type": "openai",
            "name": "My OpenAI",
            "is_enabled": True,
            "is_default": False,
            "base_url": None,
            "description": "test",
            "api_key_encrypted": "should-not-leak",
            "api_key": "should-not-leak",
            "api_key_present": True,
            "last_tested_at": None,
            "last_test_success": None,
        }
    }

    summary = summarize_user_llm_provider(snapshot)
    provider = summary["user_llm_provider"]

    assert provider["api_key_present"] is True
    assert "api_key_encrypted" not in provider
    assert "api_key" not in provider

