# UserAccessProvider Enhancements Design

**Date**: 2026-03-08
**Status**: Draft - Pending Approval
**Author**: Brainstorming session with Claude

## Overview

Enhance the UserAccessProvider system to provide a better user experience for configuring LLM provider credentials. This includes a template gallery for easy setup, full adapter configuration for power users, validation with model enumeration, pinnable favorites, and guided post-setup flows.

## Goals

1. **Reduce friction** for new users setting up their first LLM provider
2. **Expose full adapter config** for frontier providers (timeout, retries, proxy, custom headers)
3. **Validate credentials** before users proceed to dependent workflows
4. **Surface available models** with pinning for user favorites
5. **Guide users** to next steps after successful setup

## Design Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **User Journey** | Pick-and-customize gallery + power user toggle | Progressive disclosure - simple default, power when needed |
| **Templates** | Database-backed (extend LLMProviderType) | Single source of truth, admin-manageable without deploys |
| **Validation** | Tiered: quick pass/fail → expand for models/quota | Immediate feedback, depth on demand |
| **Provider Config** | Full adapter config for frontier providers | Build it right now, avoid technical debt |
| **Post-Setup** | Guided flow with quick-links + escape hatch | Reduce friction, respect power users |
| **Model Display** | Pinnable favorites | Surfaces user intent without being destructive |
| **Gallery UI** | Categorized accordions with cards | Scalable, organized by provider type |
| **Error Handling** | Provider-aware guidance + actions + diagnostics toggle | User-friendly with debug depth |

---

## Data Model Changes

### 1. LLMProviderType Extensions (Template Data)

Extend the existing `provider_type` table to serve as the template catalog:

```python
# New fields on LLMProviderType (backend/app/models.py)

category: str = Field(max_length=30)          # "major" | "cloud" | "self_hosted" | "custom"
display_name: str = Field(max_length=100)     # "OpenAI" (user-friendly)
logo_url: str | None = Field(max_length=255)  # "/assets/providers/openai.svg"
docs_url: str | None = Field(max_length=255)  # "https://platform.openai.com/docs"
default_base_url: str | None = Field(max_length=255)  # "https://api.openai.com/v1"
config_schema: dict | None = Field(sa_column=Column(JSON))  # JSON Schema for provider-specific fields
sort_order: int = Field(default=0)            # Display ordering within category
```

### 2. UserAccessProvider Extensions (Full Adapter Config)

Extend the user's provider instance:

```python
# New fields on UserAccessProvider (backend/app/models.py)

provider_config: dict | None = Field(sa_column=Column(JSON))  # Provider-specific: org_id, deployment_name, etc.
timeout_seconds: int = Field(default=30)       # Request timeout
max_retries: int = Field(default=3)            # Retry count
retry_delay_ms: int = Field(default=1000)      # Base retry delay
proxy_url: str | None = Field(max_length=255)  # Optional HTTP proxy
custom_headers: dict | None = Field(sa_column=Column(JSON))  # Additional headers

# Validation state
last_validated_at: datetime | None = None      # Last successful test timestamp
validation_error: str | None = Field(max_length=1000)  # Last error message

# Model cache
available_models_cache: list | None = Field(sa_column=Column(JSON))  # Cached model list from API
models_cached_at: datetime | None = None       # When cache was refreshed
```

### 3. New Model: UserModelPin

Track user's pinned models (follows RoomMessage pinning pattern at `models.py:3862-3893`):

```python
class UserModelPinBase(SQLModel):
    sort_order: int = Field(default=0)

class UserModelPinCreate(UserModelPinBase):
    llm_model_id: uuid.UUID

class UserModelPin(UserModelPinBase, table=True):
    __tablename__ = "user_model_pin"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    llm_model_id: uuid.UUID = Field(foreign_key="llmmodel.id", index=True)
    pinned_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "llm_model_id"),)

class UserModelPinPublic(UserModelPinBase):
    id: uuid.UUID
    user_id: uuid.UUID
    llm_model_id: uuid.UUID
    pinned_at: datetime

class UserModelPinsPublic(SQLModel):
    data: list[UserModelPinPublic]
    count: int
```

**Why User → LLMModel (not per-credential)?**
- LLMModel is already scoped to provider_type
- User with multiple OpenAI keys wants same pinned models for all
- Simpler mental model: "I like gpt-4o" not "I like gpt-4o on this key"

---

## API Endpoints

> **Implementation Note**: Review existing endpoints before implementing. Some may already exist or partially exist.

### New Validation/Testing Endpoints

Add to `/llm-providers` routes (`backend/app/api/routes/llm_providers.py`):

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/llm-providers/{provider_id}/test` | Quick pass/fail validation |
| POST | `/llm-providers/{provider_id}/test/detailed` | Full diagnostics with model list |
| GET | `/llm-providers/{provider_id}/models` | Get cached/fresh available models |

**Test endpoint response**:
```python
class TestResult(SQLModel):
    valid: bool
    error: str | None = None
    error_code: str | None = None

class DetailedTestResult(TestResult):
    models: list[ModelInfo] | None = None
    rate_limits: RateLimitInfo | None = None
    account_info: AccountInfo | None = None
```

### New Model Pinning Endpoints

Add to `/llm-catalog` routes (`backend/app/api/routes/llm_catalog.py`):

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/llm-catalog/pins` | List user's pinned models |
| POST | `/llm-catalog/pins` | Pin a model |
| DELETE | `/llm-catalog/pins/{llm_model_id}` | Unpin a model |
| PATCH | `/llm-catalog/pins/reorder` | Reorder pins |

### Enhanced Model Listing

Modify existing `GET /llm-catalog/models`:
- Add query param: `?include_pin_status=true`
- Response gains: `is_pinned: bool`, `pin_sort_order: int | null`
- Pinned models sort first when requested

---

## Frontend Components

### Reference Pattern

> **Critical**: Follow the component structure in `frontend/src/components/Agents/` (AgentsShell, AgentsHeader, AgentsLayout) for consistency.

### New: Provider Template Gallery

**Location**: `frontend/src/components/UserAccessProviders/Gallery/`

```
Gallery/
├── ProviderTemplateGallery.tsx      # Main gallery with accordions
├── ProviderCategoryAccordion.tsx    # "Major Providers", "Cloud", etc.
├── ProviderTemplateCard.tsx         # Individual provider card with "Set Up" button
└── index.ts
```

**ProviderTemplateGallery.tsx**:
- Fetches LLMProviderTypes grouped by `category`
- Renders accordion per category (Major, Cloud, Self-Hosted, Custom)
- "Power User Mode" toggle in header → shows raw form instead
- Badge showing if user already has provider configured

### Enhanced: UserAccessProvider Forms

**Location**: `frontend/src/components/UserAccessProviders/Forms/`

```
Forms/
├── UserAccessProviderForm.tsx       # Main form (enhanced with template support)
├── ProviderConfigFields.tsx         # Dynamic fields from config_schema
├── AdapterConfigSection.tsx         # Timeout, retries, proxy (collapsible)
├── ValidationPanel.tsx              # Test button + results + model list
└── index.ts
```

**ProviderConfigFields.tsx** - Provider-specific fields:
- OpenAI: `organization_id`, `project_id`
- Azure: `deployment_name`, `api_version`, `resource_name`
- Anthropic: `anthropic_version`
- Google/Vertex: `project_id`, `location`

### New: Display Components

**Location**: `frontend/src/components/UserAccessProviders/Display/`

```
Display/
├── ProviderStatusBadge.tsx          # (existing)
├── ModelBadge.tsx                   # (existing)
├── ModelPinList.tsx                 # Available models with pin toggles
├── PinnedModelChip.tsx              # Small chip for pinned model
├── ValidationDiagnostics.tsx        # Collapsible raw error/response
└── ValidationErrorPanel.tsx         # Provider-aware error guidance
```

### New: Post-Setup Flow

**Location**: `frontend/src/components/UserAccessProviders/Flows/`

```
Flows/
├── SetupSuccessPanel.tsx            # Post-validation success with quick actions
├── QuickActionCard.tsx              # Individual action option
└── index.ts
```

**Quick Actions after successful validation**:
- "Create Agent" → `/agents/new?provider={id}`
- "Browse Models" → Expand ModelPinList
- "Pin Favorites" → ModelPinList with pin UI highlighted
- "Add Another Provider" → Return to gallery
- "Skip for now" → Dismiss, return to list

---

## Error Handling

### Provider-Aware Error Guidance

```typescript
// frontend/src/components/UserAccessProviders/Display/ValidationErrorPanel.tsx

const ERROR_GUIDANCE: Record<string, Record<string, ErrorGuidance>> = {
  openai: {
    '401': {
      message: "Authentication failed",
      guidance: "Check that your API key starts with 'sk-' and hasn't been revoked",
      actions: [
        { label: "Open OpenAI Dashboard", url: "https://platform.openai.com/api-keys" },
        { label: "Retry", action: "retry" }
      ]
    },
    '429': {
      message: "Rate limit exceeded",
      guidance: "Your API key has hit its rate limit. Wait a moment or check your usage tier.",
      actions: [
        { label: "Check Usage", url: "https://platform.openai.com/usage" },
        { label: "Retry", action: "retry" }
      ]
    }
  },
  anthropic: {
    '401': {
      message: "Invalid API key",
      guidance: "Verify your key in the Anthropic Console and ensure it has API access enabled",
      actions: [
        { label: "Open Anthropic Console", url: "https://console.anthropic.com/" },
        { label: "Retry", action: "retry" }
      ]
    }
  },
  azure: {
    '404': {
      message: "Resource not found",
      guidance: "Verify your deployment name and resource URL match your Azure configuration",
      actions: [
        { label: "Open Azure Portal", url: "https://portal.azure.com/" },
        { label: "Switch to Power User Mode", action: "power_mode" }
      ]
    }
  }
  // ... extend for other providers
}
```

### Diagnostics Toggle

`ValidationDiagnostics.tsx`:
- Collapsible "Show raw response" section
- Displays: HTTP status, headers, response body (truncated)
- Copy button for sharing with support

---

## Backend Services

### Provider Adapter Pattern

**Location**: `backend/app/services/provider_adapters/`

```
provider_adapters/
├── __init__.py
├── base.py                 # Abstract ProviderAdapter class
├── openai_adapter.py       # OpenAI-specific implementation
├── anthropic_adapter.py    # Anthropic-specific
├── azure_adapter.py        # Azure OpenAI-specific
├── google_adapter.py       # Google/Vertex-specific
├── generic_adapter.py      # OpenAI-compatible fallback
└── registry.py             # Maps provider_type_id → adapter class
```

**Base adapter interface**:
```python
from abc import ABC, abstractmethod

class ProviderAdapter(ABC):
    @abstractmethod
    async def test_connection(self, config: UserAccessProvider) -> TestResult:
        """Quick validation - returns pass/fail with error details."""
        pass

    @abstractmethod
    async def list_models(self, config: UserAccessProvider) -> list[ModelInfo]:
        """Fetch available models from provider API."""
        pass

    async def get_account_info(self, config: UserAccessProvider) -> AccountInfo | None:
        """Optional: fetch account/billing info if provider supports it."""
        return None
```

---

## Migration Strategy

### Database Migrations (in order)

1. **Extend LLMProviderType** - Add template fields
2. **Extend UserAccessProvider** - Add adapter config and validation fields
3. **Create UserModelPin** - New junction table

### Data Seeding

Update existing system provider types with new template data:

```python
PROVIDER_TEMPLATES = [
    {
        "id": "673f1787-8474-4e1c-986c-8e19f14c989c",  # TYPE1 OpenAI
        "category": "major",
        "display_name": "OpenAI",
        "logo_url": "/assets/providers/openai.svg",
        "docs_url": "https://platform.openai.com/docs",
        "default_base_url": "https://api.openai.com/v1",
        "config_schema": {
            "type": "object",
            "properties": {
                "organization_id": {"type": "string", "title": "Organization ID"},
                "project_id": {"type": "string", "title": "Project ID"}
            }
        },
        "sort_order": 1
    },
    {
        "id": "008dc763-4309-43cd-ba5f-1eb1323a0964",  # TYPE2 Anthropic
        "category": "major",
        "display_name": "Anthropic",
        "logo_url": "/assets/providers/anthropic.svg",
        "docs_url": "https://docs.anthropic.com/",
        "default_base_url": "https://api.anthropic.com",
        "config_schema": {
            "type": "object",
            "properties": {
                "anthropic_version": {"type": "string", "title": "API Version", "default": "2023-06-01"}
            }
        },
        "sort_order": 2
    },
    # ... continue for other providers
]
```

---

## Implementation Notes

1. **Check existing endpoints** before implementing - some may already exist or partially exist
2. **Run `npm run generate-client`** after any backend API changes to regenerate frontend types
3. **Create Alembic migrations** for all model changes - never edit applied migrations
4. **Follow existing patterns strictly** - reference locations listed below
5. **Test validation endpoints** against real provider APIs during development

### Reference Patterns

| Pattern | Location | Notes |
|---------|----------|-------|
| Shell/Header/Layout | `frontend/src/components/Agents/` | AgentsShell, AgentsHeader, AgentsLayout |
| Pinning | `backend/app/models.py:3862-3893` | RoomMessage pinning pattern |
| CRUD functions | `backend/app/crud.py` | Functional, not class-based |
| Form components | `frontend/src/components/Agents/Forms/` | Existing form patterns |
| Selectors | `frontend/src/components/Agents/Forms/FormSelectors/` | ProviderModelSelector, ModelCombobox |
| Model hierarchy | `backend/app/models.py` | Base → Create → Update → DB → Public → Collection |

---

## Open Questions

1. **Logo assets**: Where should provider logos be stored? Options: `/public/assets/`, external CDN, base64 in database
2. **Model cache TTL**: How long should `available_models_cache` be considered fresh? Suggested: 1 hour
3. **Rate limit handling**: Should adapter config include rate limit settings, or should those be automatic?

---

## Appendix: UI Mockup

### Provider Gallery (Pick and Customize)

```
┌─────────────────────────────────────────────────────────────────┐
│  Set Up LLM Provider                    [Power User Mode ○───] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ▼ Major Providers                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ [OpenAI]    │ │ [Anthropic] │ │ [Google]    │               │
│  │             │ │             │ │             │               │
│  │ GPT-4, DALL │ │ Claude 3.5  │ │ Gemini Pro  │               │
│  │ E, Whisper  │ │ Opus, Haiku │ │ Gemma       │               │
│  │             │ │             │ │             │               │
│  │  [Set Up]   │ │  [Set Up]   │ │  [Set Up]   │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                 │
│  ▶ Cloud Platforms (Azure, AWS Bedrock, Vertex AI)             │
│                                                                 │
│  ▶ Self-Hosted (Ollama, vLLM, LocalAI)                         │
│                                                                 │
│  ▶ Custom / OpenAI-Compatible                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Post-Setup Success Panel

```
┌─────────────────────────────────────────────────────────────────┐
│  ✓ OpenAI is ready!                                  [Dismiss] │
│  12 models available • 4 with vision • 8 with function calling │
├─────────────────────────────────────────────────────────────────┤
│  What would you like to do next?                               │
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ 🤖 Create    │ │ 📋 Browse    │ │ ⭐ Pin       │            │
│  │ Agent        │ │ Models       │ │ Favorites    │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                 │
│  ┌──────────────┐                                              │
│  │ ➕ Add       │                     [Skip for now →]         │
│  │ Another      │                                              │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```
