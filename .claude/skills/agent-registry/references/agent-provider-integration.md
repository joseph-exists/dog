# Agent + LLM Provider Integration

**Completed:** January 2026

## Overview

Extended the agent system with user-selectable LLM providers and participation mode enforcement. Users can now configure their own API keys for any agent (including system agents) without affecting other users.

---

## Features Implemented

### 1. User LLM Providers

Users can store their own LLM API keys securely:

| Component | Location |
|-----------|----------|
| Model | `models.py` → `UserLLMProvider` |
| Encryption | `security.py` → `encrypt_api_key()` / `decrypt_api_key()` |
| API Routes | `llm_providers.py` |
| Frontend | `LLMProviders.tsx` in Settings → AI Providers |

**Provider Types:** `openai`, `anthropic`, `google`, `openai_compatible`

### 2. User-Agent-Provider Association

Per-user settings for agents via `UserAgentSettings`:

```
User A → StoryAdvisor → OpenAI Key #1
User B → StoryAdvisor → (system default)
User C → StoryAdvisor → OpenAI Key #2
```

| Component | Location |
|-----------|----------|
| Model | `models.py` → `UserAgentSettings` |
| API Routes | `agent_routes.py` → `/agents/{id}/my-settings` |
| Frontend | `AgentProviderSelector.tsx` |
| Service | `agent_registry_service.py` → `get_agent_for_user()` |

**Provider Resolution Fallback Chain:**
1. User's explicit `provider_id` in UserAgentSettings
2. User's default provider for that type (`is_default=True`)
3. System environment variables

### 3. Participation Mode Enforcement

Agents now respect their `participation_mode` setting:

| Mode | Behavior |
|------|----------|
| `always` | Responds to every message in the room |
| `on_mention` | Only responds when @mentioned (default) |
| `manual` | Never auto-responds; requires explicit invocation |

**@Mention Detection:**
- `@AgentSlug` - matches agent slug
- `@"Display Name"` - quoted format for names with spaces
- Case-insensitive matching

| Component | Location |
|-----------|----------|
| Detection | `agent_runner.py` → `detect_mentions()`, `is_agent_mentioned()` |
| Mode Check | `agent_runner.py` → `should_agent_respond_to_message()` |
| Entry Point | `agent_runner.py` → `run_agents_for_message()` |
| Manual Invoke | `agent_runner.py` → `invoke_agent_manually()` |

---

## Database Schema Additions

### UserLLMProvider Table
```sql
CREATE TABLE userllmprovider (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES user(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    provider_type VARCHAR NOT NULL,  -- openai, anthropic, etc.
    api_key_encrypted VARCHAR NOT NULL,
    base_url VARCHAR,
    is_default BOOLEAN DEFAULT FALSE,
    is_enabled BOOLEAN DEFAULT TRUE,
    last_test_success BOOLEAN,
    last_tested_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### UserAgentSettings Table
```sql
CREATE TABLE user_agent_settings (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES user(id) ON DELETE CASCADE,
    agent_config_id UUID REFERENCES agent_configs(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES userllmprovider(id),
    custom_system_prompt TEXT,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(user_id, agent_config_id)
);
```

---

## API Endpoints

### LLM Providers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/llm-providers/` | List user's providers |
| POST | `/api/v1/llm-providers/` | Create provider |
| GET | `/api/v1/llm-providers/{id}` | Get provider |
| PUT | `/api/v1/llm-providers/{id}` | Update provider |
| DELETE | `/api/v1/llm-providers/{id}` | Delete provider |
| POST | `/api/v1/llm-providers/{id}/test` | Test provider connection |

### Agent Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/agents/{id}/my-settings` | Get user's agent settings |
| PUT | `/api/v1/agents/{id}/my-settings` | Update user's agent settings |
| DELETE | `/api/v1/agents/{id}/my-settings` | Remove user's agent settings |

---

## Frontend Components

### AgentProviderSelector
Location: `frontend/src/components/Agents/AgentProviderSelector.tsx`

Dropdown selector for choosing LLM provider on agent detail page:
- Filters providers by required type (extracted from `model_name`)
- Shows verification status (✓/✗)
- "Use system default" option

### LLMProviders
Location: `frontend/src/components/UserSettings/LLMProviders.tsx`

Full CRUD management for user's LLM providers in Settings.

---

## Key Files Modified

| File | Changes |
|------|---------|
| `backend/app/models.py` | Added UserLLMProvider, UserAgentSettings models |
| `backend/app/api/routes/llm_providers.py` | Provider CRUD endpoints |
| `backend/app/api/routes/agent_routes.py` | Agent settings endpoints |
| `backend/app/services/agent_registry_service.py` | Provider resolution |
| `backend/app/services/agent_runner.py` | Participation mode enforcement |
| `backend/app/core/security.py` | API key encryption |
| `frontend/src/components/Agents/AgentProviderSelector.tsx` | New component |
| `frontend/src/components/UserSettings/LLMProviders.tsx` | Provider management UI |
